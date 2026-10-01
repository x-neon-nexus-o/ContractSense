from backend.app import security


def test_password_hash_is_salted_and_verifiable():
    first = security.hash_password("a-long-test-password")
    second = security.hash_password("a-long-test-password")

    assert first != second
    assert security.verify_password("a-long-test-password", first)
    assert not security.verify_password("wrong-password", first)


def test_token_signature_and_expiry_are_checked(monkeypatch):
    now = 1_800_000_000
    monkeypatch.setattr(security.time, "time", lambda: now)
    token = security.issue_token("user-1", "test-secret", ttl_hours=1)

    assert security.read_token(token, "test-secret")["sub"] == "user-1"
    assert security.read_token(token + "x", "test-secret") is None

    monkeypatch.setattr(security.time, "time", lambda: now + 3601)
    assert security.read_token(token, "test-secret") is None
