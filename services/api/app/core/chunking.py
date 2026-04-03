import re

from app.core.schemas import Chunk


def slice_pages(pages: list[str], start: int = 0, end: int | None = None) -> list[tuple[int, str]]:
    if end is None:
        end = len(pages)
    bounded_start = max(0, start)
    bounded_end = min(len(pages), end)
    return [(i, pages[i]) for i in range(bounded_start, bounded_end)]


def chunk_pages(pages_indexed: list[tuple[int, str]], pages_per_chunk: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for i in range(0, len(pages_indexed), pages_per_chunk):
        block = pages_indexed[i : i + pages_per_chunk]
        text = "\n\n".join(page_text for _, page_text in block).strip()
        if not text:
            continue
        chunks.append(
            Chunk(
                chunk_id=len(chunks) + 1,
                page_indices=[page_index for page_index, _ in block],
                text=text,
            )
        )
    return chunks


def split_text_with_page_hints(text: str, chunk_size: int = 6000) -> list[tuple[str, str]]:
    markers = list(re.finditer(r"\[\[PAGE:(\d+)\]\]", text))

    def page_for_offset(offset: int) -> str:
        current = ""
        for marker in markers:
            if marker.start() <= offset:
                current = marker.group(1)
            else:
                break
        return current

    chunks: list[tuple[str, str]] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append((text[start:end], page_for_offset(start)))
        start = end
    return chunks


def truncate_text_if_needed(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars]
