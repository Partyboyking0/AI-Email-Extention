from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    preferences: Mapped["Preference"] = relationship(back_populates="user")


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tone: Mapped[str] = mapped_column(String(24), default="formal")
    model_version: Mapped[str] = mapped_column(String(100), default="mock-phase-1")
    user: Mapped[User] = relationship(back_populates="preferences")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    email_hash: Mapped[str] = mapped_column(String(64), index=True)
    generated_reply: Mapped[str] = mapped_column(Text)
    rating: Mapped[str] = mapped_column(String(12))
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Usage(Base):
    __tablename__ = "usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    feature: Mapped[str] = mapped_column(String(32))
    count: Mapped[int] = mapped_column(Integer, default=0)


class UsageProfile(Base):
    __tablename__ = "usage_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    last_used_feature: Mapped[str] = mapped_column(String(32), default="None")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ProcessedEmail(Base):
    __tablename__ = "processed_emails"
    __table_args__ = (UniqueConstraint("user_id", "email_id", "processed_on", name="uq_processed_email_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    email_id: Mapped[str] = mapped_column(String(128))
    processed_on: Mapped[date] = mapped_column(Date)
    letters_read: Mapped[int] = mapped_column(Integer, default=0)
