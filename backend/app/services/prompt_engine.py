from backend.app.schemas.email import Tone
from backend.app.services.prompt_templates import REPLY_TEMPLATE, SUMMARY_TEMPLATE


class PromptEngine:
    def summary_prompt(self, email_text: str) -> str:
        return SUMMARY_TEMPLATE.format(email_text=email_text)

    def reply_prompt(self, email_text: str, tone: Tone) -> str:
        return REPLY_TEMPLATE.format(email_text=email_text, tone=tone)
