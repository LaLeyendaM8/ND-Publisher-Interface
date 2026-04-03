from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.core.schemas import Artifact, JobResult, JobView
from app.services.runner import RunRequest, run_tool_safe

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


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


def create_job(request: RunRequest) -> JobView:
    job_id = uuid.uuid4().hex
    job = _InternalJob(job_id=job_id, request=request)
    with _LOCK:
        _JOBS[job_id] = job
    logger.info("Job queued: %s (%s)", job_id, request.tool)
    return get_job(job_id)


def list_jobs() -> list[JobView]:
    with _LOCK:
        jobs = list(_JOBS.values())
    jobs_sorted = sorted(jobs, key=lambda j: j.created_at, reverse=True)
    return [_to_view(job) for job in jobs_sorted]


def list_jobs_for_project(project_id: str) -> list[JobView]:
    with _LOCK:
        jobs = [j for j in _JOBS.values() if j.request.project_id == project_id]
    jobs_sorted = sorted(jobs, key=lambda j: j.created_at, reverse=True)
    return [_to_view(job) for job in jobs_sorted]


def get_job(job_id: str) -> JobView:
    with _LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise KeyError(job_id)
    return _to_view(job)


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
        job = _JOBS.get(job_id)
        if job is None:
            logger.warning("Requested run for unknown job_id: %s", job_id)
            return
        job.status = "running"
        job.updated_at = _now_iso()
        request = job.request
    logger.info("Job started: %s (%s)", job_id, request.tool)

    result: JobResult = run_tool_safe(request)
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            logger.warning("Job disappeared while running: %s", job_id)
            return
        job.status = result.status
        job.message = result.message
        job.artifacts = result.artifacts
        job.updated_at = _now_iso()
    logger.info("Job finished: %s (%s)", job_id, result.status)


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
