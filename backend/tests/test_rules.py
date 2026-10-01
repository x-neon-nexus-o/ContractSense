from pathlib import Path

from backend.app.services.rules import RuleEngine


RULES_DIR = Path(__file__).resolve().parents[1] / "legal_rules"


def engine():
    return RuleEngine(RULES_DIR / "central_rules.json")


def test_msme_context_requires_explicit_supplier_selection():
    findings = engine().evaluate(
        "The invoice payment will be made within 60 days of acceptance.",
        {"contract_type": "vendor", "msme_supplier": False},
    )
    assert not any(item["rule_id"] == "MSMED_S15_PAYMENT_REVIEW" for item in findings)


def test_msme_payment_term_is_a_review_prompt_not_a_conclusion():
    findings = engine().evaluate(
        "Payment is due within 60 days after acceptance of the invoice.",
        {"contract_type": "vendor", "msme_supplier": True},
    )
    item = next(row for row in findings if row["rule_id"] == "MSMED_S15_PAYMENT_REVIEW")
    assert item["severity"] == "high"
    assert item["details"]["detected_days"] == 60
    assert item["kind"] == "deterministic_review_prompt"
    assert item["source_url"].startswith("https://www.indiacode.nic.in/")


def test_state_specific_sources_replace_generic_stamp_prompt():
    findings = engine().evaluate(
        "The parties agree to the terms of this vendor agreement.",
        {"contract_type": "vendor", "jurisdiction_state": "Maharashtra"},
    )
    ids = {item["rule_id"] for item in findings}

    assert "MH_STAMP_DUTY_SOURCE_VERIFICATION" in ids
    assert "STATE_STAMP_DUTY_VERIFICATION" not in ids
    maharashtra = next(row for row in findings if row["rule_id"] == "MH_STAMP_DUTY_SOURCE_VERIFICATION")
    assert "calculation_supported" not in maharashtra["details"]
    assert any("igrmaharashtra.gov.in" in url for url in maharashtra["source_urls"])
    assert "does not calculate" in maharashtra["message"]


def test_state_employment_prompt_is_conditional_on_state_and_contract_type():
    rules = engine()
    maharashtra = rules.evaluate(
        "This employment agreement records the parties' arrangement.",
        {"contract_type": "employment", "jurisdiction_state": "Maharashtra"},
    )
    other_state = rules.evaluate(
        "This employment agreement records the parties' arrangement.",
        {"contract_type": "employment", "jurisdiction_state": "Karnataka"},
    )

    assert any(item["rule_id"] == "MH_EMPLOYMENT_SCOPE_SOURCE_REVIEW" for item in maharashtra)
    assert not any(item["rule_id"] == "MH_EMPLOYMENT_SCOPE_SOURCE_REVIEW" for item in other_state)
    assert any(item["rule_id"] == "STATE_STAMP_DUTY_VERIFICATION" for item in other_state)


def test_unrelated_state_rule_keeps_generic_stamp_duty_prompt():
    rules = engine()
    rules.state_ruleset = {
        "ruleset_id": "test-state-rules",
        "ruleset_version": "test",
        "rules": [{
            "rule_id": "TEST_STATE_EMPLOYMENT_REVIEW",
            "state": "Karnataka",
            "law": "Synthetic test source",
            "provision": "Test applicability prompt",
            "category": "employment",
            "severity": "low",
            "message": "Synthetic test-only source review prompt.",
            "source_url": "https://example.test/source",
            "applies_to_contract_types": ["employment"],
        }],
    }

    findings = rules.evaluate(
        "The parties agree to an employment arrangement.",
        {"contract_type": "employment", "jurisdiction_state": "Karnataka"},
    )
    ids = {item["rule_id"] for item in findings}

    assert "TEST_STATE_EMPLOYMENT_REVIEW" in ids
    assert "STATE_STAMP_DUTY_VERIFICATION" in ids


def test_procurement_rules_run_by_contract_type_and_keep_multiple_sources():
    findings = engine().evaluate(
        "The parties agree the terms set out in the order.",
        {"contract_type": "procurement", "jurisdiction_state": ""},
    )
    item = next(row for row in findings if row["rule_id"] == "PUBLIC_PROCUREMENT_SOURCE_REVIEW")
    assert len(item["source_urls"]) == 2
    assert item["source_type"] == "official_procurement_material"
    assert "does not determine procurement compliance" in item["message"]


def test_unprovided_state_gets_a_generic_verification_prompt():
    findings = engine().evaluate("An ordinary commercial agreement.", {"contract_type": "other"})
    item = next(row for row in findings if row["rule_id"] == "STATE_STAMP_DUTY_VERIFICATION")
    assert item["details"]["state"] is None
    assert item["source_type"] == "official_source_index"
