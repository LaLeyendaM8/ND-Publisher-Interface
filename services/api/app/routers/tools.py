from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.auth import require_internal_token
from app.core.schemas import JobResult, JobView, ToolId
from app.core.tool_catalog import TOOL_CATALOG
from app.services.job_manager import create_job, get_job, get_job_artifact, list_jobs, run_job
from app.services.runner import RunRequest, run_tool_safe


router = APIRouter()


@router.get("")
def list_tools() -> dict[str, list[dict[str, str]]]:
    return {"tools": TOOL_CATALOG}


class ToolRunPayload(BaseModel):
    tool: ToolId
    input_path: str = Field(min_length=1)
    output_dir: str = Field(min_length=1)
    options: dict[str, Any] = Field(default_factory=dict)


@router.post("/run")
def run_tool_now(payload: ToolRunPayload, _: None = Depends(require_internal_token)) -> JobResult:
    request = RunRequest(
        tool=payload.tool,
        input_path=Path(payload.input_path),
        output_dir=Path(payload.output_dir),
        options=payload.options,
    )
    return run_tool_safe(request)


@router.post("/jobs")
def enqueue_tool_job(
    payload: ToolRunPayload,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_internal_token),
) -> JobView:
    request = RunRequest(
        tool=payload.tool,
        input_path=Path(payload.input_path),
        output_dir=Path(payload.output_dir),
        options=payload.options,
    )
    job = create_job(request, actor_user_id=None)
    background_tasks.add_task(run_job, job.job_id)
    return job


@router.get("/jobs")
def list_tool_jobs(_: None = Depends(require_internal_token)) -> dict[str, list[JobView]]:
    return {"jobs": list_jobs()}


@router.get("/jobs/{job_id}")
def get_tool_job(job_id: str, _: None = Depends(require_internal_token)) -> JobView:
    try:
        return get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}") from exc


@router.get("/jobs/{job_id}/artifacts/{artifact_index}")
def download_job_artifact(
    job_id: str,
    artifact_index: int,
    _: None = Depends(require_internal_token),
) -> FileResponse:
    try:
        artifact = get_job_artifact(job_id, artifact_index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}") from exc
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=f"Artifact not found at index: {artifact_index}") from exc

    path = Path(artifact.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact file missing: {artifact.path}")
    return FileResponse(path=str(path), filename=path.name)
