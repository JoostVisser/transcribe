"""Application settings and configuration.

Settings come from environment variables, then a `.env` file in the current
directory, then `~/.config/transcribe/.env`. The last one lets a service that
runs elsewhere (such as VidArchive's watcher) find the API keys.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def user_env_file() -> Path:
    """The `.env` file in the user's config directory."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(config_home) / "transcribe" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files take precedence over earlier ones.
        env_file=(user_env_file(), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    mistral_api_key: str = ""
