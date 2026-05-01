from typing import Literal

from pydantic import BaseModel, Field

Tone = Literal["formal", "casual", "concise"]


class EmailRequest(BaseModel):
    email_text: str = Field(min_length=1, max_length=50_000)
    thread_id: str | None = None


class SummarizeRequest(EmailRequest):
    pass


class SummaryResponse(BaseModel):
    bullets: list[str] = Field(min_length=3, max_length=3)
    model_version: str
    latency_ms: int


class ReplyRequest(EmailRequest):
    tone: Tone = "formal"


class ReplyResponse(BaseModel):
    reply: str
    tone: Tone
    model_version: str


class TaskRequest(EmailRequest):
    pass


class TaskItem(BaseModel):
    id: str
    text: str
    deadline: str | None = None
    assignee: str | None = None


class TaskResponse(BaseModel):
    tasks: list[TaskItem]
    model_version: str


class ClassifyRequest(EmailRequest):
    pass


class ClassifyResponse(BaseModel):
    label: str
    score: float = Field(ge=0, le=1)
    model_version: str = "heuristic-classifier-v1"
