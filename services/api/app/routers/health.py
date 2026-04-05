from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.db import db_conn, has_database


router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    db_status = "disabled"
    if has_database():
        try:
            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    cur.fetchone()
            db_status = "ok"
        except Exception:
            db_status = "error"

    return {
        "status": "ok",
        "env": get_settings().app_env,
        "database": db_status,
        "time": datetime.now(UTC).isoformat(),
    }
