from backend.app.services.local_reply import LocalReplyGenerator
from backend.app.services.local_summarizer import LocalSummarizer
from backend.app.services.task_extractor import HeuristicTaskExtractor


def test_local_summarizer_uses_email_content() -> None:
    email = (
        "The HireReady Newsletter shares five job search strategies for interview prep. "
        "Please review the resume checklist before Friday. "
        "The update also includes networking templates and follow-up advice."
    )
    bullets = LocalSummarizer().summarize(email)
    assert len(bullets) == 3
    assert any("resume" in bullet.lower() or "friday" in bullet.lower() for bullet in bullets)


def test_local_reply_respects_tone() -> None:
    reply = LocalReplyGenerator().reply("Can you review the proposal?", "concise")
    assert "proposal" in reply.lower()
    assert len(reply.split()) < 20


def test_task_extractor_detects_internship_invitation_actions() -> None:
    tasks = HeuristicTaskExtractor().extract(
        "TNP Cell invites students to apply for an internship. "
        "Interested students should fill out the registration form by Friday."
    )
    task_text = " ".join(task.text.lower() for task in tasks)
    assert "apply" in task_text or "fill out" in task_text
    assert any(task.deadline and "friday" in task.deadline.lower() for task in tasks)
