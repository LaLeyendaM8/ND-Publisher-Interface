from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.actor import RequestActor, require_actor
from app.core.schemas import JobView, ToolId
from app.services.job_manager import create_job, get_job_artifact, get_project_job, list_jobs_for_project, run_job
from app.services.project_manager import (
    ProjectFileView,
    ProjectView,
    create_project,
    get_file,
    get_project,
    list_project_files,
    list_projects,
    save_project_file,
)
from app.services.runner import RunRequest


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ProjectRunPayload(BaseModel):
    tool: ToolId
    file_id: str = Field(min_length=1)
    options: dict[str, Any] = Field(default_factory=dict)


@router.post("")
def create_project_now(payload: ProjectCreatePayload, actor: RequestActor = Depends(require_actor)) -> ProjectView:
    if not actor.can_write:
        raise HTTPException(status_code=403, detail="Viewer role is read-only.")
    return create_project(payload.name.strip(), workspace_id=actor.workspace_id, user_id=actor.user_id)


@router.get("")
def list_projects_now(actor: RequestActor = Depends(require_actor)) -> dict[str, list[ProjectView]]:
    return {"projects": list_projects(workspace_id=actor.workspace_id)}


@router.get("/{project_id}")
def get_project_now(project_id: str, actor: RequestActor = Depends(require_actor)) -> ProjectView:
    try:
        return get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc


@router.post("/{project_id}/files")
def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
    actor: RequestActor = Depends(require_actor),
) -> ProjectFileView:
    if not actor.can_write:
        raise HTTPException(status_code=403, detail="Viewer role is read-only.")
    try:
        return save_project_file(project_id, file, workspace_id=actor.workspace_id, user_id=actor.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc


@router.get("/{project_id}/files")
def list_files(project_id: str, actor: RequestActor = Depends(require_actor)) -> dict[str, list[ProjectFileView]]:
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    return {"files": list_project_files(project_id, workspace_id=actor.workspace_id)}


@router.get("/{project_id}/files/{file_id}")
def get_project_file(project_id: str, file_id: str, actor: RequestActor = Depends(require_actor)) -> ProjectFileView:
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    try:
        file_view = get_file(file_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}") from exc
    if file_view.project_id != project_id:
        raise HTTPException(status_code=400, detail="File does not belong to this project.")
    return file_view


@router.get("/{project_id}/files/{file_id}/download")
def download_project_file(project_id: str, file_id: str, actor: RequestActor = Depends(require_actor)) -> FileResponse:
    file_view = get_project_file(project_id, file_id, actor)
    path = Path(file_view.stored_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Stored file missing: {file_view.stored_path}")
    return FileResponse(path=str(path), filename=path.name)


@router.post("/{project_id}/jobs")
def run_project_job(
    project_id: str,
    payload: ProjectRunPayload,
    background_tasks: BackgroundTasks,
    actor: RequestActor = Depends(require_actor),
) -> JobView:
    if not actor.can_write:
        raise HTTPException(status_code=403, detail="Viewer role is read-only.")
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc

    try:
        file_view = get_file(payload.file_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {payload.file_id}") from exc
    if file_view.project_id != project_id:
        raise HTTPException(status_code=400, detail="File does not belong to this project.")

    output_dir = Path(file_view.stored_path).resolve().parent / "results" / payload.tool
    request = RunRequest(
        tool=payload.tool,
        input_path=Path(file_view.stored_path),
        output_dir=output_dir,
        options=payload.options,
        project_id=project_id,
        file_id=payload.file_id,
    )
    job = create_job(request, actor_user_id=actor.user_id)
    background_tasks.add_task(run_job, job.job_id)
    return job


@router.get("/{project_id}/jobs")
def list_project_jobs(project_id: str, actor: RequestActor = Depends(require_actor)) -> dict[str, list[JobView]]:
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    return {"jobs": list_jobs_for_project(project_id, workspace_id=actor.workspace_id)}


@router.get("/{project_id}/jobs/{job_id}")
def get_project_job_view(project_id: str, job_id: str, actor: RequestActor = Depends(require_actor)) -> JobView:
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    try:
        return get_project_job(project_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found for project: {job_id}") from exc


@router.get("/{project_id}/jobs/{job_id}/artifacts/{artifact_index}")
def download_project_job_artifact(
    project_id: str,
    job_id: str,
    artifact_index: int,
    actor: RequestActor = Depends(require_actor),
) -> FileResponse:
    try:
        get_project(project_id, workspace_id=actor.workspace_id)
        get_project_job(project_id, job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found for project: {job_id}") from exc
    try:
        artifact = get_job_artifact(job_id, artifact_index)
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=f"Artifact not found at index: {artifact_index}") from exc
    path = Path(artifact.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Artifact file missing: {artifact.path}")
    return FileResponse(path=str(path), filename=path.name)
