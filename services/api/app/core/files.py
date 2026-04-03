from pathlib import Path

import pdfplumber
from docx import Document


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_docx(path: Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def read_pdf_pages(path: Path) -> list[str]:
    pages_text: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text.replace("\u00ad", ""))
    return pages_text


def read_pdf_with_markers(path: Path) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").replace("\u00ad", "")
            pages.append(f"[[PAGE:{page_num}]]\n{text}")
    return "\n".join(pages)


def load_text_any(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return read_txt(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf_with_markers(path)
    raise ValueError(f"Unsupported file format: {suffix}")
