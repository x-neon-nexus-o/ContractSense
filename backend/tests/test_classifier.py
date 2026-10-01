from backend.app.services.classifier import ClauseClassifier, clause_risk_hint


def test_keyword_baseline_is_explicit_and_returns_a_supported_category():
    classifier = ClauseClassifier()
    prediction = classifier.classify("The customer shall pay each invoice within thirty days.")

    assert classifier.engine == "keyword_baseline"
    assert prediction["engine"] == "keyword_baseline"
    assert prediction["category"] == "Payment"
    assert 0.0 <= prediction["confidence"] <= 1.0


def test_broken_finetuned_checkpoint_falls_back_and_updates_reported_engine():
    classifier = ClauseClassifier()
    classifier.model = object()
    classifier.tokenizer = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("bad checkpoint"))
    classifier.engine = "fine_tuned_transformer"

    prediction = classifier.classify("The customer shall pay each invoice within thirty days.")

    assert prediction["category"] == "Payment"
    assert prediction["engine"] == "keyword_baseline"
    assert classifier.engine == "keyword_baseline"


def test_classifier_configuration_fingerprint_tracks_checkpoint_manifest(tmp_path):
    checkpoint = tmp_path / "local-model"
    checkpoint.mkdir()
    metadata = checkpoint / "config.json"
    metadata.write_text('{"id2label":{"0":"Payment"}}', encoding="utf-8")

    first = ClauseClassifier(str(checkpoint)).configuration_fingerprint
    metadata.write_text('{"id2label":{"0":"Termination"}}', encoding="utf-8")
    second = ClauseClassifier(str(checkpoint)).configuration_fingerprint

    assert first != second


def test_risk_hint_is_a_review_priority_signal_not_a_legal_finding():
    level, signals = clause_risk_hint("The supplier has unlimited liability.", "Liability")

    assert level == "high"
    assert signals == ["unlimited liability"]
