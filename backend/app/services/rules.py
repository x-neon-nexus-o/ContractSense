"""Versioned central/state review prompts; matches are never legal conclusions."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class RuleEngine:
    def __init__(self, rules_path: Path, state_rules_path: Path | None = None):
        self.rules_path = Path(rules_path)
        self.ruleset = json.loads(self.rules_path.read_text(encoding="utf-8"))
        self.state_rules_path = Path(state_rules_path) if state_rules_path else self.rules_path.with_name("state_rules.json")
        self.state_ruleset = {"ruleset_id": "no-state-rules", "ruleset_version": "0.0.0", "rules": []}
        if self.state_rules_path.is_file():
            self.state_ruleset = json.loads(self.state_rules_path.read_text(encoding="utf-8"))

    @property
    def info(self) -> dict[str, Any]:
        return {
            "ruleset_id": self.ruleset["ruleset_id"],
            "version": self.ruleset["ruleset_version"],
            "jurisdiction": self.ruleset["jurisdiction"],
            "last_reviewed": self.ruleset["last_reviewed"],
            "state_ruleset_id": self.state_ruleset["ruleset_id"],
            "state_ruleset_version": self.state_ruleset["ruleset_version"],
            "state_coverage": sorted({r.get("state", "") for r in self.state_ruleset.get("rules", []) if r.get("state")}),
        }

    def evaluate(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        lower = re.sub(r"\s+", " ", text.lower())
        findings: list[dict[str, Any]] = []
        state = str(metadata.get("jurisdiction_state") or "").strip()
        normalized_state = self._normalize(state)
        state_has_stamp_duty_source = any(
            self._normalize(rule.get("state", "")) == normalized_state
            and self._normalize(rule.get("category", "")) == "stamp_duty"
            for rule in self.state_ruleset.get("rules", [])
        )
        contract_type = self._normalize(metadata.get("contract_type", ""))

        for rule in self.ruleset.get("rules", []):
            rule_id = rule["rule_id"]
            # Replace the generic stamp-duty prompt only when this state has an
            # explicit stamp-duty source rule. Other state coverage (for example,
            # employment-only prompts) must not suppress the generic verification.
            if rule_id == "STATE_STAMP_DUTY_VERIFICATION" and state_has_stamp_duty_source:
                continue

            if rule_id == "MSMED_S15_PAYMENT_REVIEW":
                if not metadata.get("msme_supplier"):
                    continue
                matched = self._matches(rule.get("trigger_terms", []), lower)
                if not matched:
                    continue
                day_match = re.search(
                    r"(?:within|not later than|payment period of|paid within|due within)\s+(\d{1,3})\s*(?:calendar\s+)?days",
                    lower,
                )
                days = int(day_match.group(1)) if day_match else None
                severity = "high" if days is not None and days > 45 else "medium"
                message = rule["message"]
                if days is not None and days > 45:
                    message = (
                        f"A payment period of {days} days was detected. If the supplier is an eligible micro or small enterprise, "
                        "review this term against MSMED Act sections 15-16; this is not a legal conclusion."
                    )
                elif days is None:
                    message = (
                        "MSME-supplier context was selected, but a clear payment-period number was not extracted. "
                        "Verify the agreed date and statutory applicability under MSMED Act sections 15-16."
                    )
                findings.append(self._finding(rule, severity, message, {
                    "matched_terms": matched[:5], "detected_days": days, "supplier_context": "user-selected",
                }))
                continue

            if rule_id == "STATE_STAMP_DUTY_VERIFICATION":
                message = rule["message"]
                details = {"state": state or None, "calculation_supported": False}
                if state:
                    message = (
                        f"State-sensitive stamp-duty review is required for {state}. Confirm the instrument type, execution facts, "
                        "and current state schedule. The prototype does not calculate duty or decide registration requirements."
                    )
                else:
                    message = (
                        "No execution/performance state was supplied. Stamp duty can depend on the instrument and state; "
                        "select the relevant state and verify the current schedule. No duty is calculated."
                    )
                findings.append(self._finding(rule, "low", message, details))
                continue

            matched = self._matches(rule.get("trigger_terms", []), lower)
            applies_to_type = contract_type in {
                self._normalize(value) for value in rule.get("applies_to_contract_types", [])
            }
            if rule.get("trigger_terms") and not matched and not applies_to_type:
                continue
            if not rule.get("trigger_terms") and not applies_to_type and not rule.get("always_review"):
                continue

            severity = rule["severity"]
            message = rule["message"]
            details: dict[str, Any] = {"matched_terms": matched[:5]}
            if rule_id == "ARBITRATION_CLAUSE_COMPLETENESS_REVIEW":
                has_seat = "seat of arbitration" in lower or bool(re.search(r"seat\s+(?:shall be|is|of)\s+", lower))
                has_venue = "venue of arbitration" in lower or bool(re.search(r"venue\s+(?:shall be|is|of)\s+", lower))
                details.update({"seat_mentioned": has_seat, "venue_mentioned": has_venue})
                if not has_seat:
                    severity = "medium"
                    message = (
                        "An arbitration term was detected but a clear arbitration seat was not identified by the baseline parser. "
                        "Review the clause in context; this is not a validity finding."
                    )
            findings.append(self._finding(rule, severity, message, details))

        for rule in self.state_ruleset.get("rules", []):
            if normalized_state != self._normalize(rule.get("state", "")):
                continue
            matched = self._matches(rule.get("trigger_terms", []), lower)
            applies_to_type = contract_type in {
                self._normalize(value) for value in rule.get("applies_to_contract_types", [])
            }
            if rule.get("trigger_terms") and not matched and not applies_to_type:
                continue
            if rule.get("applies_to_contract_types") and not applies_to_type and not matched:
                continue
            if not rule.get("always_review") and not applies_to_type and not matched:
                continue
            findings.append(self._finding(rule, rule.get("severity", "low"), rule["message"], {
                "state": state,
                "matched_terms": matched[:5],
                "kind": "state_source_review_prompt",
            }))
        return findings

    def list_rules(self) -> list[dict[str, Any]]:
        rules = [*self.ruleset.get("rules", []), *self.state_ruleset.get("rules", [])]
        return [{k: v for k, v in rule.items() if k not in {"trigger_terms", "always_review"}} for rule in rules]

    def _finding(self, rule: dict[str, Any], severity: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
        source_url = rule.get("source_url", "")
        source_urls = rule.get("source_urls") or ([source_url] if source_url else [])
        return {
            "rule_id": rule["rule_id"],
            "law": rule["law"],
            "provision": rule["provision"],
            "category": rule["category"],
            "severity": severity,
            "message": message,
            "source_url": source_url,
            "source_urls": source_urls,
            "source_title": rule.get("source_title", ""),
            "source_type": rule.get("source_type", ""),
            "source_checked_on": rule.get("source_checked_on", ""),
            "ruleset_version": rule.get("version", self.ruleset.get("ruleset_version", "")),
            "details": details,
            "kind": "deterministic_review_prompt",
        }

    @staticmethod
    def _matches(terms: list[str], text: str) -> list[str]:
        return [term for term in terms if term.lower() in text]

    @staticmethod
    def _normalize(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().casefold())
