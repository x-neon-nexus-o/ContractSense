import uuid

import fitz
from fastapi.testclient import TestClient

from backend.app import main as api_main
from backend.app.main import app


client = TestClient(app)


def register(email: str) -> str:
    response = client.post("/api/v1/auth/register", json={
        "full_name": "ContractSense Test",
        "email": email,
        "password": "a-long-test-password",
    })
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_unconfigured_cors_does_not_reflect_untrusted_origins():
    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_auth_upload_analysis_chat_report_and_owner_isolation():
    owner_token = register(f"owner-{uuid.uuid4().hex}@example.test")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    assert client.get("/api/v1/contracts").status_code == 401
    assert client.get("/api/v1/auth/me", headers=owner_headers).status_code == 200

    text = (
        "VENDOR SERVICES AGREEMENT\n"
        "The parties agree that invoice payment is due within 60 days after acceptance. "
        "The supplier may terminate this agreement on written notice.\n"
        "The parties will resolve disputes through arbitration."
    )
    uploaded = client.post(
        "/api/v1/contracts/upload",
        headers=owner_headers,
        files={"file": ("vendor.txt", text.encode("utf-8"), "text/plain")},
        data={
            "contract_type": "vendor",
            "jurisdiction_state": "Maharashtra",
            "governing_law": "India",
            "msme_supplier": "true",
        },
    )
    assert uploaded.status_code == 201, uploaded.text
    contract = uploaded.json()["contract"]
    contract_id = contract["id"]

    analyzed = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=owner_headers)
    assert analyzed.status_code == 200, analyzed.text
    result = analyzed.json()["result"]
    assert result["clause_count"] >= 1
    assert result["engine"]["classifier_engine"] == "keyword_baseline"
    assert result["summary_kind"] == "opening_excerpt"
    assert result["disclaimer"]
    ids = {item["rule_id"] for item in result["legal_checks"]}
    assert "MSMED_S15_PAYMENT_REVIEW" in ids
    assert "MH_STAMP_DUTY_SOURCE_VERIFICATION" in ids
    assert "STATE_STAMP_DUTY_VERIFICATION" not in ids

    chat = client.post(
        f"/api/v1/contracts/{contract_id}/chat",
        headers=owner_headers,
        json={"message": "What does the payment and invoice term say?"},
    )
    assert chat.status_code == 200, chat.text
    chat_data = chat.json()
    assert chat_data["evidence"]
    assert chat_data["evidence"][0]["source"] == "uploaded_contract"
    assert chat_data["legal_sources"]
    history = client.get(f"/api/v1/contracts/{contract_id}/chat", headers=owner_headers)
    assert history.status_code == 200
    assistant_message = history.json()["items"][-1]
    assert assistant_message["legal_sources"] == chat_data["legal_sources"]
    assert assistant_message["provider"] == chat_data["provider"]
    assert assistant_message["limitations"] == chat_data["limitations"]

    report = client.get(f"/api/v1/contracts/{contract_id}/report", headers=owner_headers)
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("application/pdf")
    assert report.content.startswith(b"%PDF")
    with fitz.open(stream=report.content, filetype="pdf") as generated_pdf:
        report_text = "\\n".join(page.get_text() for page in generated_pdf)
    assert "Score meaning" in report_text
    assert "Opening text excerpt" in report_text
    assert "confidence (not calibrated)" in report_text

    changed = client.patch(
        f"/api/v1/contracts/{contract_id}",
        headers=owner_headers,
        json={"jurisdiction_state": "Gujarat", "msme_supplier": False},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["contract"]["analysis_stale"] is True
    current = client.get(f"/api/v1/contracts/{contract_id}", headers=owner_headers).json()
    assert current["analysis"] is None
    assert current["contract"]["analysis_id"] is None
    assert current["contract"]["status"] == "needs_reanalysis"
    assert client.get(f"/api/v1/contracts/{contract_id}/analysis", headers=owner_headers).status_code == 409
    assert client.get(f"/api/v1/contracts/{contract_id}/clauses", headers=owner_headers).status_code == 409
    assert client.get(f"/api/v1/contracts/{contract_id}/chat", headers=owner_headers).status_code == 409
    assert client.post(
        f"/api/v1/contracts/{contract_id}/chat",
        headers=owner_headers,
        json={"message": "What does the payment term say?"},
    ).status_code == 409
    assert client.get(f"/api/v1/contracts/{contract_id}/report", headers=owner_headers).status_code == 409
    assert client.get("/api/v1/dashboard/stats", headers=owner_headers).json()["analyzed_total"] == 0

    refreshed = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=owner_headers)
    assert refreshed.status_code == 200, refreshed.text
    current = client.get(f"/api/v1/contracts/{contract_id}", headers=owner_headers).json()
    assert current["contract"]["analysis_stale"] is False
    assert current["analysis"]["jurisdiction_state"] == "Gujarat"
    refreshed_rule_ids = {item["rule_id"] for item in current["analysis"]["legal_checks"]}
    assert "MSMED_S15_PAYMENT_REVIEW" not in refreshed_rule_ids
    assert "STATE_STAMP_DUTY_VERIFICATION" in refreshed_rule_ids
    assert client.get("/api/v1/dashboard/stats", headers=owner_headers).json()["analyzed_total"] == 1

    other_token = register(f"other-{uuid.uuid4().hex}@example.test")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/contracts/{contract_id}", headers=other_headers).status_code == 404

    deleted = client.delete(f"/api/v1/contracts/{contract_id}", headers=owner_headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/v1/contracts/{contract_id}", headers=owner_headers).status_code == 404


def test_pdf_page_provenance_survives_persistence_and_analysis():
    token = register(f"pages-{uuid.uuid4().hex}@example.test")
    headers = {"Authorization": f"Bearer {token}"}
    document = fitz.open()
    first = document.new_page()
    first.insert_text(
        (72, 72),
        "PAYMENT\nThe buyer shall pay each undisputed invoice within thirty days after acceptance of the deliverables.",
    )
    second = document.new_page()
    second.insert_text(
        (72, 72),
        "LIABILITY\nThe supplier's aggregate liability under this agreement is limited to the fees paid during the prior year.",
    )
    content = document.tobytes()
    document.close()

    uploaded = client.post(
        "/api/v1/contracts/upload",
        headers=headers,
        files={"file": ("two-page.pdf", content, "application/pdf")},
        data={"contract_type": "vendor", "jurisdiction_state": "Maharashtra"},
    )
    assert uploaded.status_code == 201, uploaded.text
    contract_id = uploaded.json()["contract"]["id"]
    assert uploaded.json()["contract"]["page_count"] == 2

    analyzed = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=headers)
    assert analyzed.status_code == 200, analyzed.text
    clauses = analyzed.json()["result"]["clauses"]
    assert {clause["page"] for clause in clauses} == {1, 2}


def test_classifier_configuration_change_withholds_previous_analysis(monkeypatch):
    token = register(f"classifier-{uuid.uuid4().hex}@example.test")
    headers = {"Authorization": f"Bearer {token}"}
    content = b"SERVICE AGREEMENT\nThe customer shall pay each invoice within thirty days of receipt."
    uploaded = client.post(
        "/api/v1/contracts/upload",
        headers=headers,
        files={"file": ("service.txt", content, "text/plain")},
    )
    assert uploaded.status_code == 201, uploaded.text
    contract_id = uploaded.json()["contract"]["id"]
    initial = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=headers)
    assert initial.status_code == 200, initial.text
    assert initial.json()["result"]["engine"]["classifier_config_fingerprint"]
    assert client.get(f"/api/v1/contracts/{contract_id}/analysis", headers=headers).status_code == 200

    monkeypatch.setattr(api_main.classifier, "_implementation_fingerprint", "simulated-new-classifier-code")
    assert client.get(f"/api/v1/contracts/{contract_id}/analysis", headers=headers).status_code == 409
    stale_view = client.get(f"/api/v1/contracts/{contract_id}", headers=headers).json()
    assert stale_view["analysis"] is None
    assert stale_view["contract"]["analysis_stale"] is True
    assert stale_view["contract"]["overall_risk_score"] is None

    refreshed = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=headers)
    assert refreshed.status_code == 200, refreshed.text
    assert client.get(f"/api/v1/contracts/{contract_id}/analysis", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/contracts/{contract_id}", headers=headers).json()["deleted"] is True
