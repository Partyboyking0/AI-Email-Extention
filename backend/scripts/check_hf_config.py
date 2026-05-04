import asyncio
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.core.config import settings
from backend.app.services.hf_client import HuggingFaceInferenceClient
from backend.app.services.prompt_engine import PromptEngine


async def main() -> None:
    client = HuggingFaceInferenceClient(settings.hf_api_token)
    prompts = PromptEngine()
    print("HF_API_TOKEN:", "set" if settings.hf_api_token else "missing")
    print("HF_USE_PROVIDER:", settings.hf_use_provider)
    print("HF_PROVIDER_BASE_URL:", settings.hf_provider_base_url)
    print("HF_CHAT_BASE_URL:", settings.hf_chat_base_url)
    print("HF_SUMMARIZER_MODEL:", settings.hf_summarizer_model)
    print("HF_REPLY_MODEL:", settings.hf_reply_model)
    print("HF_SUMMARIZER_ENDPOINT:", settings.hf_summarizer_endpoint or "missing")
    print("HF_REPLY_ENDPOINT:", settings.hf_reply_endpoint or "missing")

    if settings.hf_summarizer_endpoint:
        summary = await client.generate(
            str(settings.hf_summarizer_endpoint),
            "Summarize this email in 3 bullets: Please review the proposal by Friday and confirm next steps.",
            parameters={"max_new_tokens": 120},
        )
        print("\nSummarizer response:")
        print(summary[:800])

    if settings.hf_reply_endpoint:
        reply = await client.generate(
            str(settings.hf_reply_endpoint),
            "Reply to this email in a concise tone: Can you review the proposal by Friday?",
            parameters={"max_new_tokens": 160},
        )
        print("\nReply response:")
        print(reply[:800])

    if settings.hf_use_provider and settings.hf_api_token:
        try:
            provider_summary = await client.chat_completion(
                str(settings.hf_chat_base_url),
                settings.hf_reply_model,
                prompts.summary_prompt("Please review the proposal by Friday and confirm next steps."),
                max_tokens=120,
                system_prompt=(
                    "You are an email summarization assistant. "
                    "Return exactly three concise bullets grounded only in the email."
                ),
            )
            print("\nProvider summarizer response using HF_REPLY_MODEL:")
            print(provider_summary[:800])

            provider_reply = await client.chat_completion(
                str(settings.hf_chat_base_url),
                settings.hf_reply_model,
                "Reply to this email in a concise tone: Can you review the proposal by Friday?",
                max_tokens=160,
            )
            print("\nProvider reply response:")
            print(provider_reply[:800])
        except httpx.HTTPError as exc:
            print("\nProvider check failed:")
            print(f"{type(exc).__name__}: {exc}")
            if isinstance(exc, httpx.HTTPStatusError):
                print("Response body:")
                print(exc.response.text[:1200])
            print("The app will fall back to local summarization/reply generation until provider calls work.")


if __name__ == "__main__":
    asyncio.run(main())
