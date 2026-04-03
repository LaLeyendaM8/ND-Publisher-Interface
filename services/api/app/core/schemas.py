from typing import Literal

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
