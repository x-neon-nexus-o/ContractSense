"""Document analysis orchestration and transparent risk-priority calculation."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .classifier import ClauseClassifier, clause_risk_hint
from .clauses import segment_clauses

DISCLAIMER = ("ContractSense provides AI-assisted information and issue spotting only. It is not legal advice, "
              "does not determine validity or enforceability, and does not replace a qualified Indian lawyer.")


def analyze_contract(contract: dict[str, Any], classifier: ClauseClassifier, rule_engine) -> dict[str, Any]:
    text = contract.get("extracted_text", "")
    pages = contract.get("pages") or _restore_pages(text, contract.get("page_ranges", []))
    if not pages:
        pages = [{"page": 1, "text": text}]
    clauses = segment_clauses(pages)
    predictions = [classifier.classify(clause.text) for clause in clauses]
    if len({prediction["engine"] for prediction in predictions}) > 1:
        # A checkpoint can fail during inference and switch the classifier to its
        # keyword baseline. Re-run every clause so one analysis never mixes engines.
        predictions = [classifier.classify(clause.text) for clause in clauses]

    findings: list[dict[str, Any]] = []
    levels = Counter()
    for clause, prediction in zip(clauses, predictions):
        priority, signals = clause_risk_hint(clause.text, prediction["category"])
        levels[priority] += 1
        findings.append({**clause.as_dict(), "category": prediction["category"],
                         "confidence": prediction["confidence"], "classifier_engine": prediction["engine"],
                         "signals": prediction.get("signals", []), "risk_level": priority,
                         "risk_signals": signals})
    metadata = {k: contract.get(k) for k in ["contract_type", "jurisdiction_state", "governing_law", "msme_supplier"]}
    legal_checks = rule_engine.evaluate(text, metadata)
    score = 7
    for item in legal_checks:
        score += {"high": 22, "medium": 12, "low": 3}.get(item.get("severity"), 0)
    score += min(25, levels.get("high", 0) * 2 + levels.get("medium", 0))
    score = min(100, score)
    overall = "high" if score >= 65 else "medium" if score >= 35 else "low"
    category_counts = Counter(f["category"] for f in findings)
    return {
        "contract_id": contract["id"],
        "contract_name": contract["filename"],
        "contract_type": contract["contract_type"],
        "jurisdiction_state": contract.get("jurisdiction_state") or None,
        "governing_law": contract.get("governing_law") or None,
        "msme_supplier": bool(contract.get("msme_supplier", False)),
        "overall_risk_score": score,
        "overall_risk_level": overall,
        "score_label": "Review-priority indicator (not a probability or legal conclusion)",
        "summary": _opening_excerpt(text),
        "summary_kind": "opening_excerpt",
        "clause_count": len(findings),
        "category_counts": dict(category_counts),
        "risk_distribution": {"high": levels.get("high", 0), "medium": levels.get("medium", 0), "low": levels.get("low", 0)},
        "clauses": findings,
        "legal_checks": legal_checks,
        "engine": {"classifier": classifier.description, "classifier_engine": classifier.engine,
                   "classifier_config_fingerprint": classifier.configuration_fingerprint,
                   "rules": rule_engine.info, "retrieval": "indexed after analysis; local lexical or optional Chroma",
                   "risk_method": "deterministic review-priority rubric; not calibrated"},
        "coverage_notes": _coverage_notes(contract),
        "disclaimer": DISCLAIMER,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _restore_pages(text: str, ranges: list[dict[str, Any]] | None) -> list[dict[str, str | int]]:
    pages: list[dict[str, str | int]] = []
    for span in ranges or []:
        try:
            page = int(span["page"])
            start = int(span["start"])
            end = int(span["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if page < 1 or start < 0 or end <= start or end > len(text):
            continue
        page_text = text[start:end]
        if page_text.strip():
            pages.append({"page": page, "text": page_text})
    return pages


def _opening_excerpt(text: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    useful = [s for s in sentences if len(s) > 35][:3]
    result = " ".join(useful)
    return result[:1200] if result else clean[:1200]


def _coverage_notes(contract: dict[str, Any]) -> list[str]:
    notes = ["This prototype has central issue-spotting rules only; it does not provide complete pan-India legal coverage.",
             "State-specific stamp duty is not calculated. Employment and other state-specific obligations require separate verification.",
             "The classifier is a keyword baseline unless a documented fine-tuned checkpoint is configured."]
    if not contract.get("jurisdiction_state"):
        notes.append("No execution/performance state was supplied; state-dependent checks may be incomplete.")
    if contract.get("contract_type") == "vendor" and not contract.get("msme_supplier"):
        notes.append("MSME-supplier status was not selected, so the conditional MSMED payment review was not run.")
    return notes
