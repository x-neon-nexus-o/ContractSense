from backend.app.repository import SQLiteRepository


def test_sqlite_repository_scopes_contract_data_and_cascades_deletes(tmp_path):
    repo = SQLiteRepository(tmp_path / "test.sqlite3")
    try:
        user = repo.create_user("owner@example.test", "Owner", "hash")
        other = repo.create_user("other@example.test", "Other", "hash")
        contract = repo.create_contract(user["id"], "nda.txt", "/tmp/nda.txt", "nda")
        repo.save_analysis(contract["id"], user["id"], {"overall_risk_score": 17})
        repo.save_chunks(contract["id"], user["id"], [{"id": "clause-0001", "page": 1, "text": "Confidential information."}])
        evidence = [{"clause_id": "clause-0001", "page": 2, "source": "uploaded_contract"}]
        legal_sources = [{"rule_id": "RULE-1", "source_url": "https://example.test/rule"}]
        repo.save_message(contract["id"], user["id"], "assistant", "Evidence-only answer.", evidence,
                          legal_sources, "evidence_only_fallback", "No hosted provider was used.")

        assert repo.get_contract(contract["id"], user["id"])["filename"] == "nda.txt"
        assert repo.get_contract(contract["id"], other["id"]) is None
        assert repo.dashboard_stats(user["id"])["analyzed_total"] == 1
        stored_message = repo.get_messages(contract["id"], user["id"])[0]
        assert stored_message["evidence"] == evidence
        assert stored_message["legal_sources"] == legal_sources
        assert stored_message["provider"] == "evidence_only_fallback"
        assert stored_message["limitations"] == "No hosted provider was used."
        assert len(repo.get_chunks(contract["id"], user["id"])) == 1
        assert repo.delete_contract(contract["id"], user["id"])
        assert repo.get_latest_analysis(contract["id"], user["id"]) is None
        assert repo.get_chunks(contract["id"], user["id"]) == []
        assert repo.get_messages(contract["id"], user["id"]) == []
    finally:
        repo.close()


def test_existing_sqlite_database_gets_page_and_source_metadata_migrations(tmp_path):
    import sqlite3

    db_path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE contracts (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL, stored_path TEXT NOT NULL, contract_type TEXT NOT NULL,
            jurisdiction_state TEXT NOT NULL DEFAULT '', governing_law TEXT NOT NULL DEFAULT '',
            msme_supplier INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'uploaded',
            extracted_text TEXT NOT NULL DEFAULT '', page_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE messages (
            id TEXT PRIMARY KEY, contract_id TEXT NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL, content TEXT NOT NULL, evidence_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        );
        INSERT INTO users VALUES ('user-1', 'legacy@example.test', 'Legacy', 'hash', '2026-01-01');
        INSERT INTO contracts VALUES (
            'contract-1', 'user-1', 'legacy.pdf', '/tmp/legacy.pdf', 'other', '', '',
            0, 'ready', 'legacy text', 1, '2026-01-01', '2026-01-01'
        );
        INSERT INTO messages VALUES (
            'message-1', 'contract-1', 'user-1', 'assistant', 'Old answer', '[]', '2026-01-01'
        );
        """
    )
    connection.commit()
    connection.close()

    repo = SQLiteRepository(db_path)
    try:
        contract = repo.get_contract("contract-1", "user-1")
        assert contract is not None
        assert contract["extracted_text"] == "legacy text"
        assert contract["page_ranges"] == []
        old_messages = repo.get_messages("contract-1", "user-1")
        assert old_messages[0]["content"] == "Old answer"
        assert old_messages[0]["legal_sources"] == []
        assert old_messages[0]["provider"] == ""
        assert old_messages[0]["limitations"] == ""
    finally:
        repo.close()
