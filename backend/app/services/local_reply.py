from backend.app.schemas.email import Tone


class LocalReplyGenerator:
    def reply(self, email_text: str, tone: Tone) -> str:
        topic = self._topic_hint(email_text)
        if tone == "concise":
            return f"Thanks for sharing this. I’ll review {topic} and follow up with the next step shortly."
        if tone == "casual":
            return f"Thanks for sending this over. I’ll take a look at {topic} and get back to you soon."
        return (
            f"Thank you for sharing this. I will review {topic} and follow up with any questions or next steps shortly."
        )

    def _topic_hint(self, email_text: str) -> str:
        lowered = email_text.lower()
        if "meeting" in lowered:
            return "the meeting details"
        if "proposal" in lowered:
            return "the proposal"
        if "deadline" in lowered or "due" in lowered:
            return "the timeline"
        if "newsletter" in lowered:
            return "the update"
        return "the details"
