from typing import List, Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, model_validator


class Settings(BaseSettings):
    TG_TOKEN: SecretStr
    OPENAI_API_KEY: Optional[SecretStr] = None
    ADMIN_IDS: str = ""  # Будет распаршено в список
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
    # AICODE-NOTE: DATABASE_URL для Docker volume persistence
    DATABASE_URL: str = "sqlite://db.sqlite3"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_OUTPUT_TOKENS: int = 700
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"
    ANTHROPIC_MAX_OUTPUT_TOKENS: int = 700
    # AICODE-NOTE: OpenAI-совместимый эндпоинт для Anthropic,
    # прямой API блокируется (403 Forbidden)
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 5  # Максимум запросов за период
    RATE_LIMIT_PERIOD: int = 60  # Период в секундах

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """Проверяет, что API ключ для выбранного провайдера задан."""
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        return self

    @property
    def admin_ids_list(self) -> List[int]:
        """Возвращает список ID админов."""
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]


settings = Settings()
