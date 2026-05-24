from functools import lru_cache
from pathlib import Path, PureWindowsPath
from typing import Annotated, Any
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = (REPO_ROOT / ".env", REPO_ROOT / "backend" / ".env")
LOCAL_LM_STUDIO_HOSTS = {
    "127.0.0.1",
    "localhost",
    "::1",
    "host.docker.internal",
    "gateway.docker.internal",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
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
    allowed_origins: Annotated[list[str], NoDecode] = Field(
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
        return _resolve_config_path(value)

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, value: Any) -> Path:
        return _resolve_config_path(value)

    @property
    def lm_studio_is_local(self) -> bool:
        parsed_url = urlparse(str(self.lm_studio_base_url))
        return parsed_url.hostname in LOCAL_LM_STUDIO_HOSTS


def _resolve_config_path(value: Any) -> Path:
    raw_path = str(value)
    windows_path = PureWindowsPath(raw_path)
    windows_parts = list(windows_path.parts)
    lowered_parts = [part.lower() for part in windows_parts]
    repo_name = REPO_ROOT.name.lower()
    if windows_path.drive and repo_name in lowered_parts:
        repo_index = lowered_parts.index(repo_name)
        return REPO_ROOT.joinpath(*windows_parts[repo_index + 1 :])

    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
