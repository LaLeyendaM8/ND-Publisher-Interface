from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.files import ensure_dir


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "upload.bin"


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


def create_project(name: str) -> ProjectView:
    project_id = uuid.uuid4().hex
    project = _InternalProject(project_id=project_id, name=name)
    with _LOCK:
        _PROJECTS[project_id] = project
    return _to_project_view(project)


def list_projects() -> list[ProjectView]:
    with _LOCK:
        projects = list(_PROJECTS.values())
    projects_sorted = sorted(projects, key=lambda p: p.created_at, reverse=True)
    return [_to_project_view(p) for p in projects_sorted]


def get_project(project_id: str) -> ProjectView:
    with _LOCK:
        project = _PROJECTS.get(project_id)
    if project is None:
        raise KeyError(project_id)
    return _to_project_view(project)


def save_project_file(project_id: str, upload: UploadFile) -> ProjectFileView:
    with _LOCK:
        project = _PROJECTS.get(project_id)
    if project is None:
        raise KeyError(project_id)

    file_id = uuid.uuid4().hex
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
    with _LOCK:
        files = [f for f in _FILES.values() if f.project_id == project_id]
    files_sorted = sorted(files, key=lambda f: f.created_at, reverse=True)
    return [_to_file_view(f) for f in files_sorted]


def get_file(file_id: str) -> ProjectFileView:
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
