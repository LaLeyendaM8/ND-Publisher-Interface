import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


API_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(API_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    app_env: str
    openai_api_key: str | None
    internal_api_token: str | None
    storage_root: str

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        internal_api_token=os.getenv("APP_INTERNAL_API_TOKEN"),
        storage_root=os.getenv("APP_STORAGE_ROOT", str(API_ROOT / "data")),
    )


def require_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    raise RuntimeError(
        "OPENAI_API_KEY fehlt. Lege ihn in services/api/.env ab "
        "(siehe services/api/.env.example)."
    )
