from __future__ import annotations

from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from .config import Settings


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = self._build_client()

    @property
    def configured(self) -> bool:
        return bool(self.settings.openai_api_key)

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[Any]:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        kwargs: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "stream": True,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "timeout": self.settings.timeout,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return await self.client.chat.completions.create(**kwargs)

    def _build_client(self) -> AsyncOpenAI | None:
        if not self.settings.openai_api_key:
            return None
        kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key}
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url
        return AsyncOpenAI(**kwargs)
