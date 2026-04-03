from __future__ import annotations

import json
from typing import Any

from app.core.db import db_conn, has_database


def log_audit_event(
    workspace_id: str | None,
    event_name: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not has_database():
        return

    payload = metadata or {}
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_events (workspace_id, actor_user_id, event_name, entity_type, entity_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    workspace_id,
                    actor_user_id,
                    event_name,
                    entity_type,
                    entity_id,
                    json.dumps(payload),
                ),
            )
