from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.core.auth import require_internal_token
from app.core.config import get_settings
from app.core.db import db_conn, has_database


@dataclass(frozen=True)
class RequestActor:
    user_id: str
    email: str
    role: str
    workspace_id: str | None

    @property
    def can_write(self) -> bool:
        return self.role in {"admin", "editor"}


def _app_role_to_workspace_role(role: str) -> str:
    if role == "admin":
        return "owner"
    if role == "editor":
        return "editor"
    return "viewer"


def _workspace_role_to_app_role(role: str) -> str:
    if role == "owner":
        return "admin"
    if role == "editor":
        return "editor"
    return "viewer"


def _normalize_role(role: str | None) -> str:
    if role in {"admin", "editor", "viewer"}:
        return role
    return "viewer"


def _ensure_main_workspace() -> str:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO organizations (name, slug)
                VALUES (%s, %s)
                ON CONFLICT (slug)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                ("ND Internal", "nd-internal"),
            )
            org_id = str(cur.fetchone()["id"])
            cur.execute(
                """
                SELECT id
                FROM workspaces
                WHERE organization_id = %s AND slug = %s
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (org_id, "main"),
            )
            row = cur.fetchone()
            if row:
                return str(row["id"])
            cur.execute(
                """
                INSERT INTO workspaces (organization_id, name, slug)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (org_id, "Main Workspace", "main"),
            )
            return str(cur.fetchone()["id"])


def require_actor(
    x_internal_token: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_email: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> RequestActor:
    require_internal_token(x_internal_token=x_internal_token)

    # Non-DB mode keeps a fixed system actor for local development.
    if not has_database():
        return RequestActor(
            user_id=x_user_id or "system-local",
            email=x_user_email or "system@negative-dialektik.local",
            role=_normalize_role(x_user_role) if x_user_id else "admin",
            workspace_id=None,
        )

    workspace_id = _ensure_main_workspace()
    user_id = x_user_id or "00000000-0000-0000-0000-000000000001"
    email = (x_user_email or "system@negative-dialektik.local").strip().lower()
    requested_role = _normalize_role(x_user_role if x_user_id else "admin")
    requested_workspace_role = _app_role_to_workspace_role(requested_role)

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, display_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """,
                (user_id, email, email.split("@")[0]),
            )
            cur.fetchone()

            cur.execute(
                """
                SELECT role
                FROM workspace_members
                WHERE workspace_id = %s AND user_id = %s
                """,
                (workspace_id, user_id),
            )
            member = cur.fetchone()
            if not member:
                if not get_settings().auth_auto_provision_users:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User is not a workspace member.",
                    )
                cur.execute(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    VALUES (%s, %s, %s::workspace_role)
                    """,
                    (workspace_id, user_id, requested_workspace_role),
                )
                effective_workspace_role = requested_workspace_role
            else:
                effective_workspace_role = str(member["role"])

    return RequestActor(
        user_id=user_id,
        email=email,
        role=_workspace_role_to_app_role(effective_workspace_role),
        workspace_id=workspace_id,
    )
