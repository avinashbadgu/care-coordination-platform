from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "AI Care Coordination Platform"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str | None = None
    storage_dir: Path = Path("./storage")

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    default_timezone: str = "Asia/Kolkata"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        # Dev fallback: local sqlite file in the project directory.
        return "sqlite+pysqlite:///./care.sqlite"

    @property
    def is_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
