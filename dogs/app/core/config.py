from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    TG_TOKEN: SecretStr
    OPENAI_API_KEY: SecretStr
    ADMIN_IDS: List[int] = []

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
