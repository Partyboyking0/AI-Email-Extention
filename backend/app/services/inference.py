import time
import logging
import re

from backend.app.core.cache import HybridCache, cache_key
from backend.app.core.config import settings
from backend.app.schemas.email import ReplyResponse, SummaryResponse, TaskResponse, Tone
from backend.app.services.hf_client import HuggingFaceInferenceClient
from backend.app.services.local_reply import LocalReplyGenerator
from backend.app.services.local_hf import LocalHuggingFaceService
from backend.app.services.local_summarizer import LocalSummarizer
from backend.app.services.prompt_engine import PromptEngine
from backend.app.services.task_extractor import HeuristicTaskExtractor

logger = logging.getLogger(__name__)


class InferenceService:
    def __init__(self) -> None:
        self.cache = HybridCache(settings.redis_url, ttl_seconds=600)
        self.prompts = PromptEngine()
        self.hf = HuggingFaceInferenceClient(settings.hf_api_token)
        self.task_extractor = HeuristicTaskExtractor()
        self.local_summarizer = LocalSummarizer()
        self.local_reply = LocalReplyGenerator()
        self.local_hf = LocalHuggingFaceService(settings.hf_local_reply_model, settings.hf_local_reply_model)

    async def summarize(self, email_text: str, user_id: str) -> SummaryResponse:
        started = time.perf_counter()
        key = cache_key(f"summary:{user_id}", email_text)

        async def factory() -> dict[str, object]:
            if settings.hf_summarizer_endpoint:
                try:
                    generated = await self.hf.generate(
                        str(settings.hf_summarizer_endpoint),
                        self._summarizer_source(email_text),
                        parameters={"max_new_tokens": 150},
                    )
                    return {
                        "bullets": self._to_three_bullets(generated),
                        "model_version": "hf-summarizer-endpoint",
                    }
                except Exception as exc:
                    logger.warning("HF summarizer endpoint failed; falling back.", exc_info=exc)
            if settings.hf_use_provider and settings.hf_api_token:
                try:
                    generated = await self.hf.chat_completion(
                        str(settings.hf_chat_base_url),
                        settings.hf_reply_model,
                        self.prompts.summary_prompt(self._summarizer_source(email_text)),
                        max_tokens=150,
                        system_prompt=(
                            "You are an email summarization assistant. "
                            "Return exactly three concise bullets grounded only in the email."
                        ),
                    )
                    return {
                        "bullets": self._to_three_bullets(generated),
                        "model_version": f"hf-provider:{settings.hf_reply_model}",
                    }
                except Exception as exc:
                    logger.warning("HF summarizer provider failed; falling back.", exc_info=exc)
            if settings.hf_local_enabled:
                try:
                    return {
                        "bullets": self.local_hf.summarize(email_text),
                        "model_version": f"hf-local:{settings.hf_local_reply_model}",
                    }
                except Exception as exc:
                    logger.warning("Local HF summarizer failed; falling back.", exc_info=exc)

            return {
                "bullets": self.local_summarizer.summarize(email_text),
                "model_version": "local-extractive-summarizer-v1",
            }

        data = await self.cache.get_or_set(key, factory)
        return SummaryResponse(
            bullets=data["bullets"],
            model_version=data["model_version"],
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    async def reply(self, email_text: str, tone: Tone, user_id: str) -> ReplyResponse:
        prompt = self.prompts.reply_prompt(email_text, tone)
        if settings.hf_reply_endpoint:
            try:
                reply = await self.hf.generate(
                    str(settings.hf_reply_endpoint),
                    prompt,
                    parameters={"max_new_tokens": 220},
                )
                return ReplyResponse(
                    reply=self._clean_reply_text(reply),
                    tone=tone,
                    model_version="hf-reply-endpoint",
                )
            except Exception as exc:
                logger.warning("HF reply endpoint failed; falling back.", exc_info=exc)
        if settings.hf_use_provider and settings.hf_api_token:
            try:
                reply = await self.hf.chat_completion(
                    str(settings.hf_chat_base_url),
                    settings.hf_reply_model,
                    prompt,
                    max_tokens=180,
                    system_prompt=(
                        "You are an email assistant writing as the recipient. "
                        "Reply to the sender. Do not continue the original email. "
                        "Do not add subject lines, signatures, names, links, or invented facts."
                    ),
                )
                return ReplyResponse(
                    reply=self._clean_reply_text(reply),
                    tone=tone,
                    model_version=f"hf-provider:{settings.hf_reply_model}",
                )
            except Exception as exc:
                logger.warning("HF reply chat provider failed; trying provider text generation.", exc_info=exc)
            try:
                reply = await self.hf.generate_with_provider(
                    str(settings.hf_provider_base_url),
                    settings.hf_local_reply_model,
                    prompt,
                    parameters={"max_new_tokens": 180, "return_full_text": False},
                )
                return ReplyResponse(
                    reply=self._clean_reply_text(reply),
                    tone=tone,
                    model_version=f"hf-provider:{settings.hf_local_reply_model}",
                )
            except Exception as exc:
                logger.warning("HF reply text provider failed; falling back.", exc_info=exc)
        if settings.hf_local_enabled:
            try:
                return ReplyResponse(
                    reply=self.local_hf.reply(email_text, tone),
                    tone=tone,
                    model_version=f"hf-local:{settings.hf_local_reply_model}",
                )
            except Exception as exc:
                logger.warning("Local HF reply generator failed; falling back.", exc_info=exc)

        return ReplyResponse(
            reply=self.local_reply.reply(email_text, tone),
            tone=tone,
            model_version="local-reply-generator-v1",
        )

    async def tasks(self, email_text: str, user_id: str) -> TaskResponse:
        return TaskResponse(
            tasks=self.task_extractor.extract(email_text),
            model_version="heuristic-task-extractor-v1",
        )

    def _to_three_bullets(self, generated: str) -> list[str]:
        banned_fragments = (
            "summarization assistant",
            "extract the most actionable",
            "output exactly",
            "each bullet",
            "start with",
            "email start",
            "email end",
            "bullet points",
            "tags to choose",
        )
        candidates = [
            self._clean_summary_item(line)
            for line in generated.splitlines()
            if self._clean_summary_item(line) and not any(fragment in line.lower() for fragment in banned_fragments)
        ]
        if len(candidates) < 3:
            candidates = [
                self._clean_summary_item(part)
                for part in generated.split(".")
                if self._clean_summary_item(part) and not any(fragment in part.lower() for fragment in banned_fragments)
            ]

        bullets = candidates[:3]
        while len(bullets) < 3:
            bullets.append("Review the email context and confirm the next action.")
        return bullets

    def _clean_summary_item(self, item: str) -> str:
        cleaned = item.strip()
        return re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", cleaned).strip()

    def _summarizer_source(self, email_text: str) -> str:
        return email_text[:12_000]

    def _clean_reply_text(self, generated: str) -> str:
        lines = []
        for line in generated.replace("\r", "\n").splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered.startswith("subject:"):
                continue
            if lowered.startswith("dear [") or lowered in {"qwen", "best regards,", "best regards"}:
                continue
            if lowered.startswith(("sincerely", "regards,")):
                continue
            lines.append(cleaned)

        reply = " ".join(lines).strip()
        reply = re.sub(r"\s*\[[^\]]*(?:name|recipient|signature)[^\]]*\]\s*", " ", reply, flags=re.IGNORECASE)
        reply = re.sub(r"\s{2,}", " ", reply).strip()
        return reply or "Thank you for sharing this. I will review the details and follow up shortly."
