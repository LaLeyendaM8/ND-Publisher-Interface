from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI
from openpyxl import Workbook
from openpyxl.styles import Font

from app.core.chunking import split_text_with_page_hints
from app.core.config import require_openai_api_key
from app.core.files import ensure_dir, load_text_any
from app.core.retry import call_with_retries
from app.core.schemas import Artifact, JobResult


SYSTEM_PROMPT = """
Realiza una revision final exclusivamente gramatical, ortografica y ortotipografica del texto.

La traduccion y la edicion ya estan terminadas.
No debes reescribir ni modificar el estilo.
Solo detecta errores verificables.

Debes devolver unicamente JSON valido con esta forma:
{
  "errors": [
    {
      "pagina": "12",
      "ubicacion_exacta": "frase o linea exacta",
      "fragmento_con_error": "fragmento breve",
      "tipo_de_error": "ortografico | gramatical | ortotipografico | puntuacion | espacios",
      "correccion_exacta": "solo la correccion exacta"
    }
  ]
}

Si no hay errores, devuelve: {"errors":[]}
""".strip()


@dataclass
class ProofcheckConfig:
    model: str = "gpt-5-mini"
    chunk_size: int = 6000
    retries: int = 3


def _extract_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```").strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    return json.loads(raw)


def _review_chunk(client: OpenAI, cfg: ProofcheckConfig, chunk: str, page_hint: str) -> list[dict[str, Any]]:
    prompt = f"""
Pagina aproximada del fragmento: {page_hint if page_hint else "N/A"}

Revisa este fragmento y devuelve solo JSON valido.

TEXTO:
{chunk}
""".strip()
    resp = call_with_retries(
        lambda: client.responses.create(
            model=cfg.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        ),
        retries=cfg.retries,
        base_sleep_seconds=1.5,
    )
    payload = _extract_json(resp.output_text)
    errors = payload.get("errors", [])
    for err in errors:
        if not err.get("pagina") and page_hint:
            err["pagina"] = page_hint
    return errors


def _dedupe_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for err in errors:
        key = (
            str(err.get("pagina", "")),
            str(err.get("ubicacion_exacta", "")),
            str(err.get("fragmento_con_error", "")),
            str(err.get("tipo_de_error", "")),
            str(err.get("correccion_exacta", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(err)
    return unique


def _save_report_xlsx(errors: list[dict[str, Any]], output_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Lektorat"
    headers = [
        "pagina",
        "ubicacion_exacta",
        "fragmento_con_error",
        "tipo_de_error",
        "correccion_exacta",
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for err in errors:
        ws.append(
            [
                err.get("pagina", ""),
                err.get("ubicacion_exacta", ""),
                err.get("fragmento_con_error", ""),
                err.get("tipo_de_error", ""),
                err.get("correccion_exacta", ""),
            ]
        )
    widths = {"A": 12, "B": 40, "C": 60, "D": 22, "E": 40}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    wb.save(str(output_path))


def run_proofcheck_job(input_path: Path, output_dir: Path, cfg: ProofcheckConfig | None = None) -> JobResult:
    cfg = cfg or ProofcheckConfig()
    ensure_dir(output_dir)
    api_key = require_openai_api_key()
    client = OpenAI(api_key=api_key)

    text = load_text_any(input_path)
    chunks = split_text_with_page_hints(text, cfg.chunk_size)
    all_errors: list[dict[str, Any]] = []
    for chunk_text, page_hint in chunks:
        all_errors.extend(_review_chunk(client, cfg, chunk_text, page_hint))
    unique_errors = _dedupe_errors(all_errors)

    out_json = output_dir / "lektorat_report.json"
    out_xlsx = output_dir / "lektorat_report.xlsx"
    out_json.write_text(json.dumps({"errors": unique_errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    _save_report_xlsx(unique_errors, out_xlsx)

    return JobResult(
        tool="proofcheck",
        status="done",
        message=f"Proofcheck completed ({len(unique_errors)} findings)",
        artifacts=[
            Artifact(kind="json", path=str(out_json)),
            Artifact(kind="xlsx", path=str(out_xlsx)),
        ],
    )
