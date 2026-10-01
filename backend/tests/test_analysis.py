from __future__ import annotations

from pathlib import Path

from backend.app.services.analysis import analyze_contract
from backend.app.services.rules import RuleEngine


class FlakyClassifier:
    def __init__(self) -> None:
        self.engine = "fine_tuned_transformer"
        self.calls = 0

    @property
    def description(self) -> str:
        return f"test classifier ({self.engine})"

    @property
    def configuration_fingerprint(self) -> str:
        return f"test-config-{self.engine}"

    def classify(self, text: str) -> dict[str, object]:
        self.calls += 1
        if self.calls == 2:
            self.engine = "keyword_baseline"
        category = "Payment" if "payment" in text.lower() or "invoice" in text.lower() else "Termination"
        return {
            "category": category,
            "confidence": 0.5,
            "engine": self.engine,
            "signals": [],
        }


def test_analysis_restarts_all_clauses_on_midrun_classifier_fallback() -> None:
    classifier = FlakyClassifier()
    rules_path = Path(__file__).resolve().parents[1] / "legal_rules" / "central_rules.json"
    rules = RuleEngine(rules_path)
    contract = {
        "id": "test-contract",
        "filename": "two-clauses.txt",
        "contract_type": "vendor",
        "extracted_text": "",
        "pages": [{
            "page": 1,
            "text": (
                "PAYMENT\nThe customer shall pay each invoice within thirty days of receipt. "
                "The supplier must send invoice details.\n\n"
                "TERMINATION\nEither party may terminate this agreement after written notice. "
                "The parties will return confidential information."
            ),
        }],
    }

    result = analyze_contract(contract, classifier, rules)

    assert result["clause_count"] == 2
    assert classifier.calls == 4
    assert {clause["classifier_engine"] for clause in result["clauses"]} == {"keyword_baseline"}
    assert result["engine"]["classifier_engine"] == "keyword_baseline"
    assert result["engine"]["classifier_config_fingerprint"] == "test-config-keyword_baseline"
