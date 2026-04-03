from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.db import db_conn, has_database
from app.core.files import ensure_dir
from app.services.audit_service import log_audit_event


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "upload.bin"


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


class ProjectView(BaseModel):
    project_id: str
    name: str
    created_at: str
    updated_at: str


class ProjectFileView(BaseModel):
    file_id: str
    project_id: str
    original_name: str
    stored_path: str
    size_bytes: int = Field(ge=0)
    created_at: str


@dataclass
class _InternalProject:
    project_id: str
    name: str
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class _InternalProjectFile:
    file_id: str
    project_id: str
    original_name: str
    stored_path: str
    size_bytes: int
    created_at: str = field(default_factory=_now_iso)


_PROJECTS: dict[str, _InternalProject] = {}
_FILES: dict[str, _InternalProjectFile] = {}
_LOCK = threading.Lock()


def _storage_root() -> Path:
    root = Path(get_settings().storage_root)
    ensure_dir(root)
    return root


def _ensure_default_workspace_context() -> tuple[str, str]:
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
                INSERT INTO users (email, display_name)
                VALUES (%s, %s)
                ON CONFLICT (email)
                DO UPDATE SET display_name = EXCLUDED.display_name
                RETURNING id
                """,
                ("system@negative-dialektik.local", "ND System"),
            )
            user_id = str(cur.fetchone()["id"])

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
                workspace_id = str(row["id"])
            else:
                cur.execute(
                    """
                    INSERT INTO workspaces (organization_id, name, slug)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (org_id, "Main Workspace", "main"),
                )
                workspace_id = str(cur.fetchone()["id"])

            cur.execute(
                """
                INSERT INTO workspace_members (workspace_id, user_id, role)
                VALUES (%s, %s, 'owner')
                ON CONFLICT (workspace_id, user_id) DO NOTHING
                """,
                (workspace_id, user_id),
            )
    return workspace_id, user_id


def _create_project_db(name: str) -> ProjectView:
    workspace_id, user_id = _ensure_default_workspace_context()
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (workspace_id, name, created_by)
                VALUES (%s, %s, %s)
                RETURNING id, name, created_at, updated_at
                """,
                (workspace_id, name, user_id),
            )
            row = cur.fetchone()
    view = ProjectView(
        project_id=str(row["id"]),
        name=row["name"],
        created_at=_to_iso(row["created_at"]),
        updated_at=_to_iso(row["updated_at"]),
    )
    log_audit_event(
        workspace_id=workspace_id,
        actor_user_id=user_id,
        event_name="project.created",
        entity_type="project",
        entity_id=view.project_id,
        metadata={"name": view.name},
    )
    return view


def _list_projects_db() -> list[ProjectView]:
    workspace_id, _ = _ensure_default_workspace_context()
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, created_at, updated_at
                FROM projects
                WHERE workspace_id = %s
                ORDER BY created_at DESC
                """,
                (workspace_id,),
            )
            rows = cur.fetchall()
    return [
        ProjectView(
            project_id=str(r["id"]),
            name=r["name"],
            created_at=_to_iso(r["created_at"]),
            updated_at=_to_iso(r["updated_at"]),
        )
        for r in rows
    ]


def _get_project_db(project_id: str) -> ProjectView:
    workspace_id, _ = _ensure_default_workspace_context()
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, created_at, updated_at
                FROM projects
                WHERE id = %s AND workspace_id = %s
                """,
                (project_id, workspace_id),
            )
            row = cur.fetchone()
    if not row:
        raise KeyError(project_id)
    return ProjectView(
        project_id=str(row["id"]),
        name=row["name"],
        created_at=_to_iso(row["created_at"]),
        updated_at=_to_iso(row["updated_at"]),
    )


def _save_project_file_db(project_id: str, upload: UploadFile) -> ProjectFileView:
    project = _get_project_db(project_id)
    workspace_id, user_id = _ensure_default_workspace_context()

    file_id = str(uuid.uuid4())
    filename = _safe_filename(upload.filename or "upload.bin")
    target_dir = _storage_root() / "uploads" / workspace_id / project.project_id
    ensure_dir(target_dir)
    target = target_dir / f"{file_id}_{filename}"

    size = 0
    with target.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            out.write(chunk)

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO files (id, project_id, original_name, size_bytes, storage_path, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, project_id, original_name, size_bytes, storage_path, created_at
                """,
                (file_id, project.project_id, upload.filename or filename, size, str(target), user_id),
            )
            row = cur.fetchone()
    view = ProjectFileView(
        file_id=str(row["id"]),
        project_id=str(row["project_id"]),
        original_name=row["original_name"],
        stored_path=row["storage_path"],
        size_bytes=int(row["size_bytes"]),
        created_at=_to_iso(row["created_at"]),
    )
    log_audit_event(
        workspace_id=workspace_id,
        actor_user_id=user_id,
        event_name="file.uploaded",
        entity_type="file",
        entity_id=view.file_id,
        metadata={
            "project_id": view.project_id,
            "original_name": view.original_name,
            "size_bytes": view.size_bytes,
        },
    )
    return view


def _list_project_files_db(project_id: str) -> list[ProjectFileView]:
    _get_project_db(project_id)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, original_name, size_bytes, storage_path, created_at
                FROM files
                WHERE project_id = %s
                ORDER BY created_at DESC
                """,
                (project_id,),
            )
            rows = cur.fetchall()
    return [
        ProjectFileView(
            file_id=str(r["id"]),
            project_id=str(r["project_id"]),
            original_name=r["original_name"],
            stored_path=r["storage_path"],
            size_bytes=int(r["size_bytes"]),
            created_at=_to_iso(r["created_at"]),
        )
        for r in rows
    ]


def _get_file_db(file_id: str) -> ProjectFileView:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, original_name, size_bytes, storage_path, created_at
                FROM files
                WHERE id = %s
                """,
                (file_id,),
            )
            row = cur.fetchone()
    if not row:
        raise KeyError(file_id)
    return ProjectFileView(
        file_id=str(row["id"]),
        project_id=str(row["project_id"]),
        original_name=row["original_name"],
        stored_path=row["storage_path"],
        size_bytes=int(row["size_bytes"]),
        created_at=_to_iso(row["created_at"]),
    )


def create_project(name: str) -> ProjectView:
    if has_database():
        return _create_project_db(name)

    project_id = str(uuid.uuid4())
    project = _InternalProject(project_id=project_id, name=name)
    with _LOCK:
        _PROJECTS[project_id] = project
    return _to_project_view(project)


def list_projects() -> list[ProjectView]:
    if has_database():
        return _list_projects_db()

    with _LOCK:
        projects = list(_PROJECTS.values())
    projects_sorted = sorted(projects, key=lambda p: p.created_at, reverse=True)
    return [_to_project_view(p) for p in projects_sorted]


def get_project(project_id: str) -> ProjectView:
    if has_database():
        return _get_project_db(project_id)

    with _LOCK:
        project = _PROJECTS.get(project_id)
    if project is None:
        raise KeyError(project_id)
    return _to_project_view(project)


def save_project_file(project_id: str, upload: UploadFile) -> ProjectFileView:
    if has_database():
        return _save_project_file_db(project_id, upload)

    with _LOCK:
        project = _PROJECTS.get(project_id)
    if project is None:
        raise KeyError(project_id)

    file_id = str(uuid.uuid4())
    filename = _safe_filename(upload.filename or "upload.bin")
    project_dir = _storage_root() / "uploads" / project_id
    ensure_dir(project_dir)
    target = project_dir / f"{file_id}_{filename}"

    size = 0
    with target.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            out.write(chunk)

    record = _InternalProjectFile(
        file_id=file_id,
        project_id=project_id,
        original_name=upload.filename or filename,
        stored_path=str(target),
        size_bytes=size,
    )
    with _LOCK:
        _FILES[file_id] = record
        project.updated_at = _now_iso()
        _PROJECTS[project_id] = project
    return _to_file_view(record)


def list_project_files(project_id: str) -> list[ProjectFileView]:
    if has_database():
        return _list_project_files_db(project_id)

    with _LOCK:
        files = [f for f in _FILES.values() if f.project_id == project_id]
    files_sorted = sorted(files, key=lambda f: f.created_at, reverse=True)
    return [_to_file_view(f) for f in files_sorted]


def get_file(file_id: str) -> ProjectFileView:
    if has_database():
        return _get_file_db(file_id)

    with _LOCK:
        file_rec = _FILES.get(file_id)
    if file_rec is None:
        raise KeyError(file_id)
    return _to_file_view(file_rec)


def _to_project_view(project: _InternalProject) -> ProjectView:
    return ProjectView(
        project_id=project.project_id,
        name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _to_file_view(file_rec: _InternalProjectFile) -> ProjectFileView:
    return ProjectFileView(
        file_id=file_rec.file_id,
        project_id=file_rec.project_id,
        original_name=file_rec.original_name,
        stored_path=file_rec.stored_path,
        size_bytes=file_rec.size_bytes,
        created_at=file_rec.created_at,
    )
