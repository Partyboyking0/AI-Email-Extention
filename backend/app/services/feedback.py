import hashlib
from dataclasses import dataclass

from backend.app.schemas.users import FeedbackRequest


@dataclass(frozen=True)
class FeedbackRecord:
    user_id: str
    email_hash: str
    generated_reply: str
    rating: str
    reason: str | None


class FeedbackService:
    def __init__(self) -> None:
        self._records: list[FeedbackRecord] = []

    def add(self, user_id: str, payload: FeedbackRequest) -> FeedbackRecord:
        email_hash = hashlib.sha256(payload.email_text.encode("utf-8")).hexdigest()
        record = FeedbackRecord(
            user_id=user_id,
            email_hash=email_hash,
            generated_reply=payload.generated_reply,
            rating=payload.rating,
            reason=payload.reason,
        )
        self._records.append(record)
        return record

    def count(self, user_id: str | None = None) -> int:
        if user_id is None:
            return len(self._records)
        return sum(1 for record in self._records if record.user_id == user_id)
