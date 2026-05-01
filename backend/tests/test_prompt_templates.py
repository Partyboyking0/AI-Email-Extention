from backend.app.services.prompt_templates import REPLY_TEMPLATE, SUMMARY_TEMPLATE


def test_summary_template_injects_email_text() -> None:
    prompt = SUMMARY_TEMPLATE.format(email_text="Please bring ID card tomorrow.")
    assert "Please bring ID card tomorrow." in prompt
    assert "Output bullet points" in prompt
    assert "[EMAIL START]" in prompt
    assert "[EMAIL END]" in prompt


def test_reply_template_injects_tone_and_email_text() -> None:
    prompt = REPLY_TEMPLATE.format(tone="formal", email_text="Can you review the seating plan?")
    assert "formal reply" in prompt
    assert "Can you review the seating plan?" in prompt
    assert "person who received the email" in prompt
    assert "not continuing it" in prompt
