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
    database_url: str | None
    supabase_service_role_key: str | None
    retention_artifact_days: int
    retention_failed_job_days: int
    retention_audit_days: int

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        internal_api_token=os.getenv("APP_INTERNAL_API_TOKEN"),
        storage_root=os.getenv("APP_STORAGE_ROOT", str(API_ROOT / "data")),
        database_url=os.getenv("DATABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        retention_artifact_days=int(os.getenv("RETENTION_ARTIFACT_DAYS", "180")),
        retention_failed_job_days=int(os.getenv("RETENTION_FAILED_JOB_DAYS", "30")),
        retention_audit_days=int(os.getenv("RETENTION_AUDIT_DAYS", "365")),
    )


def require_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    raise RuntimeError(
        "OPENAI_API_KEY fehlt. Lege ihn in services/api/.env ab "
        "(siehe services/api/.env.example)."
    )
