from __future__ import annotations

import abc
import ssl
import warnings
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import httpx
import structlog
from openai import AsyncOpenAI, DefaultAsyncHttpxClient

# Suppress SSL warnings for corporate networks
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# AICODE-NOTE: Больше не используем нативный anthropic SDK,
# работаем через OpenAI-совместимый API с кастомным base_url


# AICODE-NOTE: Disable SSL verification for corporate networks with proxy/firewall
# that intercept HTTPS traffic with self-signed certificates.
# In production, this should be replaced with proper certificate handling.
def _create_ssl_context() -> ssl.SSLContext:
    """Create SSL context that doesn't verify certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _create_insecure_http_client() -> DefaultAsyncHttpxClient:
    """Create HTTP client that skips SSL verification."""
    # AICODE-NOTE: Используем DefaultAsyncHttpxClient из OpenAI SDK
    # чтобы корректно передавались заголовки авторизации
    return DefaultAsyncHttpxClient(
        verify=False,
        timeout=httpx.Timeout(60.0, connect=30.0),
    )

ChatMessage = dict[str, str]


@dataclass(slots=True)
class LLMResponse:
    text: str
    raw: Any
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


class BaseLLMClient(abc.ABC):
    provider: str
    model: str

    @abc.abstractmethod
    async def complete(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        ...


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.provider = "openai"
        self.model = model
        # Use insecure client for corporate networks with SSL interception
        self._client = AsyncOpenAI(
            api_key=api_key,
            http_client=_create_insecure_http_client(),
        )
        self.log = structlog.get_logger("OpenAIClient")

    async def complete(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        prepared = list(messages)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=prepared,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )
        message = response.choices[0].message
        text = message.content or ""
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        return LLMResponse(
            text=text,
            raw=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


class AnthropicClient(BaseLLMClient):
    """
    Клиент для Anthropic через OpenAI-совместимый API.
    
    AICODE-NOTE: Прямой Anthropic API блокируется (403 Forbidden),
    поэтому используем OpenAI Python SDK с кастомным base_url
    для доступа к Anthropic-совместимому эндпоинту.
    """
    
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.provider = "anthropic"
        self.model = model
        # AICODE-NOTE: Используем AsyncOpenAI с кастомным base_url
        # для работы с Anthropic через OpenRouter.
        # Корпоративный прокси перехватывает SSL, поэтому:
        # 1. Отключаем SSL проверку через http_client
        # 2. Явно добавляем Authorization в заголовки (иначе не передаётся)
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://t.me/GistBot_bot",
                "X-Title": "GistBot",
            },
            http_client=_create_insecure_http_client(),
        )
        self.log = structlog.get_logger("AnthropicClient")

    async def complete(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        # OpenAI-совместимый API использует стандартный формат messages
        prepared = list(messages)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=prepared,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )
        message = response.choices[0].message
        text = message.content or ""
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        return LLMResponse(
            text=text,
            raw=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


