from backend.app.services.preprocessor import EmailPreprocessor


def test_preprocessor_scrubs_pii_and_signature() -> None:
    text = "<p>Email me at person@example.com or +1 555 123 4567</p><p>Best regards<br>Alex</p>"
    cleaned = EmailPreprocessor().clean(text)
    assert "[EMAIL]" in cleaned
    assert "[PHONE]" in cleaned
    assert "Alex" not in cleaned
