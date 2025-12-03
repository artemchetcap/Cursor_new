from __future__ import annotations

import abc
import ssl
import warnings
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

import httpx
import structlog
from openai import AsyncOpenAI

# Suppress SSL warnings for corporate networks
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

try:
    from anthropic import AsyncAnthropic
except ImportError:  # pragma: no cover - optional dependency
    AsyncAnthropic = None


# AICODE-NOTE: Disable SSL verification for corporate networks with proxy/firewall
# that intercept HTTPS traffic with self-signed certificates.
# In production, this should be replaced with proper certificate handling.
def _create_ssl_context() -> ssl.SSLContext:
    """Create SSL context that doesn't verify certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _create_insecure_http_client() -> httpx.AsyncClient:
    """Create HTTP client that skips SSL verification."""
    return httpx.AsyncClient(
        verify=_create_ssl_context(),
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
    def __init__(self, api_key: str, model: str) -> None:
        if AsyncAnthropic is None:
            raise ImportError("anthropic package is not installed")
        self.provider = "anthropic"
        self.model = model
        self._client = AsyncAnthropic(api_key=api_key)
        self.log = structlog.get_logger("AnthropicClient")

    async def complete(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
    ) -> LLMResponse:
        prepared = list(messages)
        system_prompt = self._pluck_system_prompt(prepared)
        anthropic_messages = self._map_messages(prepared)
        response = await self._client.messages.create(
            system=system_prompt,
            model=self.model,
            messages=anthropic_messages,
            temperature=temperature,
            max_output_tokens=max_output_tokens or 1024,
        )
        text = self._merge_response_text(response.content)
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None) if usage else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage else None
        return LLMResponse(
            text=text,
            raw=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _pluck_system_prompt(self, messages: List[ChatMessage]) -> str:
        for message in messages:
            if message.get("role") == "system":
                return message.get("content", "")
        return ""

    def _map_messages(self, messages: List[ChatMessage]) -> List[dict]:
        mapped: List[dict] = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                continue
            mapped.append({"role": role or "user", "content": message.get("content", "")})
        return mapped

    def _merge_response_text(self, blocks: Any) -> str:
        parts: List[str] = []
        for block in blocks:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()


