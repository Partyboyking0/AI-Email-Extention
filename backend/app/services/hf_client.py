from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


class HuggingFaceInferenceClient:
    def __init__(self, api_token: str | None, timeout_seconds: float = 15.0) -> None:
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds

    async def generate(self, endpoint: str, inputs: str, parameters: dict[str, Any] | None = None) -> str:
        async def call_model(prompt: str) -> str:
            return await self._post_generate(endpoint, prompt, parameters or {})

        chain = RunnableLambda(call_model) | StrOutputParser()
        return await chain.ainvoke(inputs)

    async def generate_with_provider(
        self,
        base_url: str,
        model_id: str,
        inputs: str,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        model_path = quote(model_id, safe="/")
        endpoint = f"{base_url.rstrip('/')}/{model_path}"
        return await self.generate(endpoint, inputs, parameters)

    async def chat_completion(
        self,
        endpoint: str,
        model: str,
        prompt: str,
        max_tokens: int = 180,
        system_prompt: str | None = None,
    ) -> str:
        async def call_model(text: str) -> str:
            return await self._post_chat_completion(endpoint, model, text, max_tokens, system_prompt)

        chain = RunnableLambda(call_model) | StrOutputParser()
        return await chain.ainvoke(prompt)

    async def _post_generate(self, endpoint: str, inputs: str, parameters: dict[str, Any]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json={"inputs": inputs, "parameters": parameters},
            )
            response.raise_for_status()
            payload = response.json()

        return self._extract_text(payload)

    async def _post_chat_completion(
        self,
        endpoint: str,
        model: str,
        prompt: str,
        max_tokens: int,
        system_prompt: str | None,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()

        choices = payload.get("choices", []) if isinstance(payload, dict) else []
        if choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict) and message.get("content"):
                return str(message["content"])
            if choices[0].get("text"):
                return str(choices[0]["text"])
        return self._extract_text(payload)

    def _extract_text(self, payload: Any) -> str:
        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, dict):
                return str(
                    first.get("generated_text")
                    or first.get("summary_text")
                    or first.get("translation_text")
                    or first.get("text")
                    or first
                )
            return str(first)

        if isinstance(payload, dict):
            return str(
                payload.get("generated_text")
                or payload.get("summary_text")
                or payload.get("text")
                or payload.get("answer")
                or payload
            )

        return str(payload)
