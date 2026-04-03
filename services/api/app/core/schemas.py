from typing import Any, Literal

from pydantic import BaseModel, Field


ToolId = Literal["translation", "bibliography", "proofcheck"]
JobStatus = Literal["queued", "running", "done", "failed"]


class Chunk(BaseModel):
    chunk_id: int = Field(ge=1)
    page_indices: list[int]
    text: str


class Artifact(BaseModel):
    kind: str
    path: str


class JobResult(BaseModel):
    tool: ToolId
    status: JobStatus
    message: str = ""
    artifacts: list[Artifact] = Field(default_factory=list)


class JobView(BaseModel):
    job_id: str
    tool: ToolId
    status: JobStatus
    project_id: str | None = None
    file_id: str | None = None
    input_path: str
    output_dir: str
    options: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    artifacts: list[Artifact] = Field(default_factory=list)
    created_at: str
    updated_at: str
