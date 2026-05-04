from datetime import UTC, date, datetime
import hashlib
import math

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app.models.user import Feedback, Preference, ProcessedEmail, Usage, UsageProfile, User
from backend.app.schemas.users import FeedbackRequest, PreferenceRequest, PreferenceResponse, UsageRequest, UsageStatsResponse


LETTERS_READ_PER_SAVED_MINUTE = 900


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

    def record_usage(self, subject: str, payload: UsageRequest) -> UsageStatsResponse:
        user = self.get_or_create_user(subject)
        self.record_last_used_feature(user, payload.feature)
        self.record_feature_count(user, payload.feature)
        self.record_email_metrics(user, payload)
        self.session.flush()
        return self.usage_stats(subject)

    def record_last_used_feature(self, user: User, feature: str) -> None:
        profile = self.session.scalar(select(UsageProfile).where(UsageProfile.user_id == user.id))
        if profile is None:
            profile = UsageProfile(user_id=user.id)
            self.session.add(profile)

        profile.last_used_feature = feature
        profile.updated_at = datetime.now(UTC)

    def record_feature_count(self, user: User, feature: str) -> None:
        usage = self.session.scalar(select(Usage).where(Usage.user_id == user.id, Usage.feature == feature))
        if usage is None:
            usage = Usage(user_id=user.id, feature=feature, count=0)
            self.session.add(usage)

        usage.count += 1

    def record_email_metrics(self, user: User, payload: UsageRequest) -> None:
        email_id = payload.email_id or f"{payload.feature}:{datetime.now(UTC).timestamp()}"
        today = date.today()
        processed_email = self.session.scalar(
            select(ProcessedEmail).where(
                ProcessedEmail.user_id == user.id,
                ProcessedEmail.email_id == email_id,
                ProcessedEmail.processed_on == today,
            )
        )
        if processed_email is not None:
            processed_email.letters_read = max(processed_email.letters_read, payload.letters_read)
            return

        self.session.add(
            ProcessedEmail(
                user_id=user.id,
                email_id=email_id,
                processed_on=today,
                letters_read=payload.letters_read,
            )
        )

    def usage_stats(self, subject: str) -> UsageStatsResponse:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is None:
            return UsageStatsResponse(
                processed_today=0,
                time_saved_minutes=0,
                most_used_feature="None",
                last_used_feature="None",
                by_feature={},
            )

        rows = self.session.scalars(select(Usage).where(Usage.user_id == user.id)).all()
        by_feature = {row.feature: row.count for row in rows}
        most_used = max(by_feature.items(), key=lambda item: item[1])[0] if by_feature else "None"
        profile = self.session.scalar(select(UsageProfile).where(UsageProfile.user_id == user.id))
        processed = int(
            self.session.scalar(
                select(func.count(ProcessedEmail.id)).where(
                    ProcessedEmail.user_id == user.id,
                    ProcessedEmail.processed_on == date.today(),
                )
            )
            or 0
        )
        letters_read = int(
            self.session.scalar(
                select(func.coalesce(func.sum(ProcessedEmail.letters_read), 0)).where(
                    ProcessedEmail.user_id == user.id,
                    ProcessedEmail.processed_on == date.today(),
                )
            )
            or 0
        )
        return UsageStatsResponse(
            processed_today=processed,
            time_saved_minutes=math.ceil(letters_read / LETTERS_READ_PER_SAVED_MINUTE) if letters_read else 0,
            most_used_feature=self.format_feature(most_used),
            last_used_feature=self.format_feature(profile.last_used_feature if profile else "None"),
            by_feature=by_feature,
        )

    def reset_usage(self, subject: str) -> UsageStatsResponse:
        user = self.get_or_create_user(subject)
        self.session.execute(delete(ProcessedEmail).where(ProcessedEmail.user_id == user.id))
        self.session.execute(delete(Usage).where(Usage.user_id == user.id))
        profile = self.session.scalar(select(UsageProfile).where(UsageProfile.user_id == user.id))
        if profile is not None:
            profile.last_used_feature = "None"
            profile.updated_at = datetime.now(UTC)
        self.session.flush()
        return self.usage_stats(subject)

    def format_feature(self, feature: str | None) -> str:
        if not feature or feature == "None":
            return "None"
        return feature[:1].upper() + feature[1:]

    def delete_user_data(self, subject: str) -> None:
        user = self.session.scalar(select(User).where(User.google_subject == subject))
        if user is None:
            return

        self.session.execute(delete(Feedback).where(Feedback.user_id == user.id))
        self.session.execute(delete(Preference).where(Preference.user_id == user.id))
        self.session.execute(delete(Usage).where(Usage.user_id == user.id))
        self.session.execute(delete(UsageProfile).where(UsageProfile.user_id == user.id))
        self.session.execute(delete(ProcessedEmail).where(ProcessedEmail.user_id == user.id))
        self.session.delete(user)
