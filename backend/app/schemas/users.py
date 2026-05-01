from typing import Literal

from pydantic import BaseModel, Field

Tone = Literal["formal", "casual", "concise"]
Rating = Literal["up", "down"]
Feature = Literal["summarize", "reply", "tasks", "classify"]


class PreferenceRequest(BaseModel):
    tone: Tone = "formal"
    model_version: str = "mock-phase-1"


class PreferenceResponse(PreferenceRequest):
    user_id: str


class FeedbackRequest(BaseModel):
    email_text: str = Field(min_length=1, max_length=50_000)
    generated_reply: str = Field(min_length=1)
    rating: Rating
    reason: str | None = None


class UsageRequest(BaseModel):
    feature: Feature


class UsageStatsResponse(BaseModel):
    processed_today: int
    time_saved_minutes: int
    most_used_feature: str
    by_feature: dict[str, int]
