from __future__ import annotations

from typing import Iterable, Optional

import structlog

from app.core.config import Settings, settings

from .client import AnthropicClient, BaseLLMClient, LLMResponse, OpenAIClient
from .prompt import DEEP_ANALYSIS_PROMPT
from .token_counter import TokenCounter
from .types import SummaryPayload, SummaryResult, TokenUsage


class LLMService:
    """
    Provider-agnostic summarization service.
    """

    def __init__(
        self,
        client: BaseLLMClient,
        *,
        token_counter: Optional[TokenCounter] = None,
        max_output_tokens: int = 800,
        temperature: float = 0.3,
    ) -> None:
        self.client = client
        self.token_counter = token_counter or TokenCounter(client.model)
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.log = structlog.get_logger("LLMService")

    async def summarize(self, payload: SummaryPayload) -> SummaryResult:
        messages = self._build_messages(payload)
        response = await self.client.complete(
            messages,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )
        token_usage = self._resolve_token_usage(messages, response)
        return SummaryResult(
            text=response.text.strip(),
            tokens=token_usage,
            model=self.client.model,
        )

    def _build_messages(self, payload: SummaryPayload) -> list[dict[str, str]]:
        metadata_section = "\n".join(
            f"- {key}: {value}"
            for key, value in payload.metadata.items()
            if value not in (None, "", [])
        ) or "- none"

        user_prompt = (
            f"Тип контента: {payload.content_type.value}\n"
            f"Заголовок: {payload.title}\n"
            f"Источник: {payload.source_url or 'n/a'}\n"
            f"Метаданные:\n{metadata_section}\n\n"
            f"Текст:\n{payload.content.strip()}"
        )
        return [
            {"role": "system", "content": DEEP_ANALYSIS_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _resolve_token_usage(self, messages: Iterable[dict[str, str]], response: LLMResponse) -> TokenUsage:
        prompt_tokens = response.prompt_tokens or self.token_counter.count_messages(messages)
        completion_tokens = response.completion_tokens or self.token_counter.count_text(response.text)
        return TokenUsage(prompt=prompt_tokens, completion=completion_tokens)


def build_llm_service(active_settings: Optional[Settings] = None) -> LLMService:
    cfg = active_settings or settings
    provider = cfg.LLM_PROVIDER.lower()

    if provider == "openai":
        client = OpenAIClient(
            api_key=cfg.OPENAI_API_KEY.get_secret_value(),
            model=cfg.OPENAI_MODEL,
        )
        max_tokens = cfg.OPENAI_MAX_OUTPUT_TOKENS
    elif provider == "anthropic":
        if cfg.ANTHROPIC_API_KEY is None:
            raise ValueError("ANTHROPIC_API_KEY is required when provider=anthropic")
        client = AnthropicClient(
            api_key=cfg.ANTHROPIC_API_KEY.get_secret_value(),
            model=cfg.ANTHROPIC_MODEL,
            base_url=cfg.ANTHROPIC_BASE_URL,
        )
        max_tokens = cfg.ANTHROPIC_MAX_OUTPUT_TOKENS
    else:
        raise ValueError(f"Unsupported LLM provider: {cfg.LLM_PROVIDER}")

    return LLMService(
        client=client,
        token_counter=TokenCounter(client.model),
        max_output_tokens=max_tokens,
    )


