from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.db import db_conn, has_database
from app.core.schemas import Artifact, JobResult, JobView
from app.services.audit_service import log_audit_event
from app.services.runner import RunRequest, run_tool_safe

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


@dataclass
class _InternalJob:
    job_id: str
    request: RunRequest
    status: str = "queued"
    message: str = ""
    artifacts: list[Artifact] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


_JOBS: dict[str, _InternalJob] = {}
_LOCK = threading.Lock()


def _is_db_job_candidate(request: RunRequest) -> bool:
    return has_database() and request.project_id is not None


def _create_job_db(request: RunRequest) -> JobView:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT workspace_id FROM projects WHERE id = %s", (request.project_id,))
            project_row = cur.fetchone()
            if not project_row:
                raise KeyError(request.project_id)
            workspace_id = str(project_row["workspace_id"])

            job_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO jobs (id, workspace_id, project_id, file_id, tool, status, options, message)
                VALUES (%s, %s, %s, %s, %s, 'queued', %s::jsonb, '')
                RETURNING id, project_id, file_id, tool, status, options, message, queued_at
                """,
                (
                    job_id,
                    workspace_id,
                    request.project_id,
                    request.file_id,
                    request.tool,
                    json.dumps(request.options),
                ),
            )
            row = cur.fetchone()
    view = JobView(
        job_id=str(row["id"]),
        tool=row["tool"],
        status=row["status"],
        project_id=str(row["project_id"]) if row["project_id"] else None,
        file_id=str(row["file_id"]) if row["file_id"] else None,
        input_path=str(request.input_path),
        output_dir=str(request.output_dir),
        options=row["options"] or {},
        message=row["message"] or "",
        artifacts=[],
        created_at=_to_iso(row["queued_at"]),
        updated_at=_to_iso(row["queued_at"]),
    )
    log_audit_event(
        workspace_id=workspace_id,
        actor_user_id=None,
        event_name="job.queued",
        entity_type="job",
        entity_id=view.job_id,
        metadata={
            "project_id": view.project_id,
            "file_id": view.file_id,
            "tool": view.tool,
        },
    )
    return view


def create_job(request: RunRequest) -> JobView:
    if _is_db_job_candidate(request):
        logger.info("Job queued in DB for project=%s tool=%s", request.project_id, request.tool)
        return _create_job_db(request)

    job_id = uuid.uuid4().hex
    job = _InternalJob(job_id=job_id, request=request)
    with _LOCK:
        _JOBS[job_id] = job
    logger.info("In-memory job queued: %s (%s)", job_id, request.tool)
    return get_job(job_id)


def _artifact_size(path: str) -> int:
    p = Path(path)
    if p.exists() and p.is_file():
        return p.stat().st_size
    return 0


def _fetch_job_row(job_id: str) -> dict[str, Any] | None:
    if not has_database():
        return None
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, file_id, tool, status, options, message, queued_at,
                       COALESCE(finished_at, started_at, queued_at) AS updated_at
                FROM jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            return cur.fetchone()


def _fetch_artifacts(job_id: str) -> list[Artifact]:
    if not has_database():
        return []
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT kind, storage_path
                FROM artifacts
                WHERE job_id = %s
                ORDER BY created_at ASC
                """,
                (job_id,),
            )
            rows = cur.fetchall()
    return [Artifact(kind=r["kind"], path=r["storage_path"]) for r in rows]


def _job_view_from_row(row: dict[str, Any]) -> JobView:
    return JobView(
        job_id=str(row["id"]),
        tool=row["tool"],
        status=row["status"],
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        file_id=str(row["file_id"]) if row.get("file_id") else None,
        input_path="",
        output_dir="",
        options=row.get("options") or {},
        message=row.get("message") or "",
        artifacts=_fetch_artifacts(str(row["id"])),
        created_at=_to_iso(row["queued_at"]),
        updated_at=_to_iso(row["updated_at"]),
    )


def list_jobs() -> list[JobView]:
    items: list[JobView] = []
    if has_database():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, file_id, tool, status, options, message, queued_at,
                           COALESCE(finished_at, started_at, queued_at) AS updated_at
                    FROM jobs
                    ORDER BY queued_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
        items.extend(_job_view_from_row(r) for r in rows)

    with _LOCK:
        mem_jobs = list(_JOBS.values())
    mem_sorted = sorted(mem_jobs, key=lambda j: j.created_at, reverse=True)
    items.extend(_to_view(j) for j in mem_sorted)
    return items


def list_jobs_for_project(project_id: str) -> list[JobView]:
    if has_database():
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, file_id, tool, status, options, message, queued_at,
                           COALESCE(finished_at, started_at, queued_at) AS updated_at
                    FROM jobs
                    WHERE project_id = %s
                    ORDER BY queued_at DESC
                    """,
                    (project_id,),
                )
                rows = cur.fetchall()
        return [_job_view_from_row(r) for r in rows]

    with _LOCK:
        jobs = [j for j in _JOBS.values() if j.request.project_id == project_id]
    jobs_sorted = sorted(jobs, key=lambda j: j.created_at, reverse=True)
    return [_to_view(job) for job in jobs_sorted]


def get_job(job_id: str) -> JobView:
    with _LOCK:
        job = _JOBS.get(job_id)
    if job is not None:
        return _to_view(job)

    row = _fetch_job_row(job_id)
    if row is None:
        raise KeyError(job_id)
    return _job_view_from_row(row)


def get_project_job(project_id: str, job_id: str) -> JobView:
    job = get_job(job_id)
    if job.project_id != project_id:
        raise KeyError(job_id)
    return job


def get_job_artifact(job_id: str, artifact_index: int) -> Artifact:
    view = get_job(job_id)
    if artifact_index < 0 or artifact_index >= len(view.artifacts):
        raise IndexError(artifact_index)
    return view.artifacts[artifact_index]


def run_job(job_id: str) -> None:
    with _LOCK:
        mem_job = _JOBS.get(job_id)
        if mem_job:
            mem_job.status = "running"
            mem_job.updated_at = _now_iso()
            request = mem_job.request
        else:
            request = None

    if request is None:
        row = _fetch_job_row(job_id)
        if row is None:
            logger.warning("Requested run for unknown job_id: %s", job_id)
            return
        if row.get("status") == "running":
            logger.info("Job already running: %s", job_id)
            return
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status='running', started_at=NOW() WHERE id=%s",
                    (job_id,),
                )
                cur.execute(
                    "SELECT tool, options, project_id, file_id FROM jobs WHERE id=%s",
                    (job_id,),
                )
                meta = cur.fetchone()
        if not meta:
            logger.warning("Job metadata missing for job_id=%s", job_id)
            return
        # For DB jobs, rebuild paths from project/file storage entries.
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT storage_path, project_id FROM files WHERE id = %s",
                    (meta["file_id"],),
                )
                file_row = cur.fetchone()
        if not file_row:
            result = JobResult(tool=meta["tool"], status="failed", message="File missing for job", artifacts=[])
        else:
            file_path = Path(file_row["storage_path"])
            output_dir = file_path.resolve().parent / "results" / meta["tool"]
            request = RunRequest(
                tool=meta["tool"],
                input_path=file_path,
                output_dir=output_dir,
                options=meta.get("options") or {},
                project_id=str(meta["project_id"]) if meta.get("project_id") else None,
                file_id=str(meta["file_id"]) if meta.get("file_id") else None,
            )
            result = run_tool_safe(request)

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status=%s, message=%s, finished_at=NOW() WHERE id=%s",
                    (result.status, result.message, job_id),
                )
                cur.execute("DELETE FROM artifacts WHERE job_id=%s", (job_id,))
                for artifact in result.artifacts:
                    cur.execute(
                        """
                        INSERT INTO artifacts (job_id, kind, storage_path, size_bytes)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (job_id, artifact.kind, artifact.path, _artifact_size(artifact.path)),
                    )
                cur.execute("SELECT workspace_id FROM jobs WHERE id=%s", (job_id,))
                workspace_row = cur.fetchone()
                workspace_id = str(workspace_row["workspace_id"]) if workspace_row else None
        log_audit_event(
            workspace_id=workspace_id,
            actor_user_id=None,
            event_name="job.finished",
            entity_type="job",
            entity_id=job_id,
            metadata={"status": result.status, "message": result.message, "artifacts": len(result.artifacts)},
        )
        logger.info("DB job finished: %s (%s)", job_id, result.status)
        return

    logger.info("In-memory job started: %s (%s)", job_id, request.tool)
    result = run_tool_safe(request)
    with _LOCK:
        mem_job = _JOBS.get(job_id)
        if mem_job is None:
            logger.warning("In-memory job disappeared: %s", job_id)
            return
        mem_job.status = result.status
        mem_job.message = result.message
        mem_job.artifacts = result.artifacts
        mem_job.updated_at = _now_iso()
    logger.info("In-memory job finished: %s (%s)", job_id, result.status)


def _to_view(job: _InternalJob) -> JobView:
    return JobView(
        job_id=job.job_id,
        tool=job.request.tool,
        status=job.status,  # type: ignore[arg-type]
        project_id=job.request.project_id,
        file_id=job.request.file_id,
        input_path=str(job.request.input_path),
        output_dir=str(job.request.output_dir),
        options=job.request.options,
        message=job.message,
        artifacts=job.artifacts,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
