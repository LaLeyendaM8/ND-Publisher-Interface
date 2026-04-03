from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.schemas import JobResult, ToolId
from app.services.bibliography_service import BibliographyConfig, run_bibliography_job
from app.services.proofcheck_service import ProofcheckConfig, run_proofcheck_job
from app.services.translation_service import TranslationConfig, run_translation_job

logger = logging.getLogger(__name__)


class _TranslationOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    glossary_path: str | None = None
    pages_per_chunk: int | None = None
    model: str | None = None
    temperature: float | None = None
    timeout_seconds: float | None = None
    retries: int | None = None
    retry_base_sleep: float | None = None
    max_chars_per_chunk: int | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    add_chunk_headers: bool | None = None
    page_start: int | None = None
    page_end: int | None = None


class _BibliographyOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pages_per_chunk: int | None = None
    model: str | None = None
    temperature: float | None = None
    timeout_seconds: float | None = None
    retries: int | None = None
    retry_base_sleep: float | None = None
    max_chars_per_chunk: int | None = None
    add_chunk_headers: bool | None = None
    page_start: int | None = None
    page_end: int | None = None


class _ProofcheckOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    chunk_size: int | None = None
    retries: int | None = None


@dataclass
class RunRequest:
    tool: ToolId
    input_path: Path
    output_dir: Path
    options: dict[str, Any]
    project_id: str | None = None
    file_id: str | None = None


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "invalid value")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts)


def _build_translation_config(options: dict[str, Any]) -> tuple[TranslationConfig, Path | None]:
    parsed = _TranslationOptions.model_validate(options)
    data = parsed.model_dump(exclude_none=True)
    glossary_path_raw = data.pop("glossary_path", None)
    glossary_path = Path(glossary_path_raw) if isinstance(glossary_path_raw, str) and glossary_path_raw else None
    return TranslationConfig(**data), glossary_path


def _build_bibliography_config(options: dict[str, Any]) -> BibliographyConfig:
    parsed = _BibliographyOptions.model_validate(options)
    return BibliographyConfig(**parsed.model_dump(exclude_none=True))


def _build_proofcheck_config(options: dict[str, Any]) -> ProofcheckConfig:
    parsed = _ProofcheckOptions.model_validate(options)
    return ProofcheckConfig(**parsed.model_dump(exclude_none=True))


def _validate_input(request: RunRequest) -> None:
    if not request.input_path.exists():
        raise FileNotFoundError(f"Input not found: {request.input_path}")
    if request.tool in {"translation", "bibliography"} and request.input_path.suffix.lower() != ".pdf":
        raise ValueError(f"{request.tool} expects a PDF input file.")


def run_tool(request: RunRequest) -> JobResult:
    _validate_input(request)

    if request.tool == "translation":
        try:
            cfg, glossary_path = _build_translation_config(request.options)
        except ValidationError as exc:
            raise ValueError(f"Invalid translation options: {_format_validation_error(exc)}") from exc
        return run_translation_job(
            pdf_path=request.input_path,
            output_dir=request.output_dir,
            glossary_path=glossary_path,
            cfg=cfg,
        )

    if request.tool == "bibliography":
        try:
            cfg = _build_bibliography_config(request.options)
        except ValidationError as exc:
            raise ValueError(f"Invalid bibliography options: {_format_validation_error(exc)}") from exc
        return run_bibliography_job(
            pdf_path=request.input_path,
            output_dir=request.output_dir,
            cfg=cfg,
        )

    if request.tool == "proofcheck":
        try:
            cfg = _build_proofcheck_config(request.options)
        except ValidationError as exc:
            raise ValueError(f"Invalid proofcheck options: {_format_validation_error(exc)}") from exc
        return run_proofcheck_job(
            input_path=request.input_path,
            output_dir=request.output_dir,
            cfg=cfg,
        )

    raise ValueError(f"Unsupported tool: {request.tool}")


def run_tool_safe(request: RunRequest) -> JobResult:
    try:
        return run_tool(request)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Tool run rejected (%s): %s", request.tool, exc)
        return JobResult(tool=request.tool, status="failed", message=str(exc), artifacts=[])
    except RuntimeError as exc:
        logger.error("Tool runtime error (%s): %s", request.tool, exc)
        return JobResult(tool=request.tool, status="failed", message=str(exc), artifacts=[])
    except Exception as exc:  # noqa: BLE001
        logger.exception("Tool run crashed (%s)", request.tool)
        return JobResult(tool=request.tool, status="failed", message=f"Unexpected error: {exc}", artifacts=[])
