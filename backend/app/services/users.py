import hashlib

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app.models.user import Feedback, Preference, Usage, User
from backend.app.schemas.users import FeedbackRequest, PreferenceRequest, PreferenceResponse, UsageStatsResponse


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_user(self, subject: str) -> User:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is not None:
            return user

        user = User(google_subject=subject)
        self.session.add(user)
        self.session.flush()
        return user

    def get_preferences(self, subject: str) -> PreferenceResponse:
        user = self.get_or_create_user(subject)
        preference = self.session.scalar(select(Preference).where(Preference.user_id == user.id))
        if preference is None:
            preference = Preference(user_id=user.id)
            self.session.add(preference)
            self.session.flush()

        return PreferenceResponse(
            user_id=subject,
            tone=preference.tone,
            model_version=preference.model_version,
        )

    def save_preferences(self, subject: str, payload: PreferenceRequest) -> PreferenceResponse:
        user = self.get_or_create_user(subject)
        preference = self.session.scalar(select(Preference).where(Preference.user_id == user.id))
        if preference is None:
            preference = Preference(user_id=user.id)
            self.session.add(preference)

        preference.tone = payload.tone
        preference.model_version = payload.model_version
        self.session.flush()
        return PreferenceResponse(user_id=subject, tone=preference.tone, model_version=preference.model_version)

    def save_feedback(self, subject: str, payload: FeedbackRequest) -> int:
        user = self.get_or_create_user(subject)
        email_hash = hashlib.sha256(payload.email_text.encode("utf-8")).hexdigest()
        self.session.add(
            Feedback(
                user_id=user.id,
                email_hash=email_hash,
                generated_reply=payload.generated_reply,
                rating=payload.rating,
                reason=payload.reason,
            )
        )
        self.session.flush()
        return self.feedback_count(subject)

    def feedback_count(self, subject: str) -> int:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is None:
            return 0
        count = self.session.scalar(select(func.count(Feedback.id)).where(Feedback.user_id == user.id))
        return int(count or 0)

    def record_usage(self, subject: str, feature: str) -> UsageStatsResponse:
        user = self.get_or_create_user(subject)
        usage = self.session.scalar(select(Usage).where(Usage.user_id == user.id, Usage.feature == feature))
        if usage is None:
            usage = Usage(user_id=user.id, feature=feature, count=0)
            self.session.add(usage)

        usage.count += 1
        self.session.flush()
        return self.usage_stats(subject)

    def usage_stats(self, subject: str) -> UsageStatsResponse:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is None:
            return UsageStatsResponse(
                processed_today=0,
                time_saved_minutes=0,
                most_used_feature="None",
                by_feature={},
            )

        rows = self.session.scalars(select(Usage).where(Usage.user_id == user.id)).all()
        by_feature = {row.feature: row.count for row in rows}
        processed = sum(by_feature.values())
        most_used = max(by_feature.items(), key=lambda item: item[1])[0] if by_feature else "None"
        return UsageStatsResponse(
            processed_today=processed,
            time_saved_minutes=processed * 2,
            most_used_feature=most_used.title(),
            by_feature=by_feature,
        )

    def delete_user_data(self, subject: str) -> None:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is None:
            return

        self.session.execute(delete(Feedback).where(Feedback.user_id == user.id))
        self.session.execute(delete(Preference).where(Preference.user_id == user.id))
        self.session.execute(delete(Usage).where(Usage.user_id == user.id))
        self.session.delete(user)
