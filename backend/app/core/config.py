from pydantic import AnyHttpUrl, Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    allowed_origins: list[str] = Field(default_factory=lambda: ["chrome-extension://development", "http://localhost:5173"])
    allowed_origin_regex: str = r"chrome-extension://.*"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./backend/app.db"
    demo_auth_subject: str = "phase-1-demo-user"
    environment: str = "local"
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0
    hf_summarizer_endpoint: AnyHttpUrl | None = None
    hf_reply_endpoint: AnyHttpUrl | None = None
    hf_api_token: str | None = None
    hf_use_provider: bool = False
    hf_provider_base_url: AnyHttpUrl = "https://router.huggingface.co/hf-inference/models"
    hf_chat_base_url: AnyHttpUrl = "https://router.huggingface.co/v1/chat/completions"
    hf_summarizer_model: str = "sshleifer/distilbart-cnn-12-6"
    hf_reply_model: str = "katanemo/Arch-Router-1.5B:hf-inference"
    hf_local_enabled: bool = False
    hf_local_summarizer_model: str = "google/flan-t5-small"
    hf_local_reply_model: str = "google/flan-t5-small"

    @field_validator("hf_summarizer_endpoint", "hf_reply_endpoint", "sentry_dsn", "hf_api_token", mode="before")
    @classmethod
    def empty_url_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            return None
        return value


settings = Settings()
