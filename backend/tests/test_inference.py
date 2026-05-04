import pytest

from backend.app.core.config import settings
from backend.app.services.inference import InferenceService


class FakeHuggingFaceClient:
    def __init__(self) -> None:
        self.chat_calls: list[dict[str, object]] = []

    async def chat_completion(
        self,
        endpoint: str,
        model: str,
        prompt: str,
        max_tokens: int = 180,
        system_prompt: str | None = None,
    ) -> str:
        self.chat_calls.append(
            {
                "endpoint": endpoint,
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "system_prompt": system_prompt,
            }
        )
        return "- **Context** Proposal needs review\n- **Deadline** Friday\n- **Next Step** Confirm next steps"


@pytest.mark.anyio
async def test_provider_summarize_uses_reply_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "hf_summarizer_endpoint", None)
    monkeypatch.setattr(settings, "hf_use_provider", True)
    monkeypatch.setattr(settings, "hf_api_token", "test-token")
    monkeypatch.setattr(settings, "hf_local_enabled", False)
    monkeypatch.setattr(settings, "hf_reply_model", "reply-model:test-provider")
    monkeypatch.setattr(settings, "hf_summarizer_model", "old-summary-model")

    service = InferenceService()
    fake_hf = FakeHuggingFaceClient()
    service.hf = fake_hf

    response = await service.summarize(
        "Please review the proposal by Friday and confirm next steps.",
        user_id="provider-summary-test",
    )

    assert response.model_version == "hf-provider:reply-model:test-provider"
    assert response.bullets == [
        "**Context** Proposal needs review",
        "**Deadline** Friday",
        "**Next Step** Confirm next steps",
    ]
    assert fake_hf.chat_calls[0]["model"] == "reply-model:test-provider"
    assert "old-summary-model" not in str(fake_hf.chat_calls[0])


def test_local_hf_summarizer_uses_local_reply_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "hf_local_summarizer_model", "old-local-summary-model")
    monkeypatch.setattr(settings, "hf_local_reply_model", "local-reply-model")

    service = InferenceService()

    assert service.local_hf.summarizer_model == "local-reply-model"
    assert service.local_hf.reply_model == "local-reply-model"
