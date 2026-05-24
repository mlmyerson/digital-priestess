from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "127.0.0.1"
    app_port: int = 8787
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    lm_studio_model: str = "local-model"
    lm_studio_timeout_seconds: float = 60.0
    archive_root: Path | None = None
    data_dir: Path = Path(".local/data")
    enable_ocr: bool = False
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"]
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("archive_root", mode="before")
    @classmethod
    def empty_archive_root_is_none(cls, value: Any) -> Path | None:
        if value in (None, ""):
            return None
        return Path(value).expanduser()

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, value: Any) -> Path:
        return Path(value).expanduser()

    @property
    def lm_studio_is_local(self) -> bool:
        parsed_url = urlparse(str(self.lm_studio_base_url))
        return parsed_url.hostname in {"127.0.0.1", "localhost", "::1"}


@lru_cache
def get_settings() -> Settings:
    return Settings()