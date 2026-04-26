from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from src.ingestion.normalizer import SOURCE_TYPES, clean_text


DEFAULT_CHUNK_SIZE_CHARS = 1600
DEFAULT_CHUNK_OVERLAP_CHARS = 240


@dataclass(frozen=True)
class ChunkedDocument:
    chunk_id: str
    document_id: str
    chunk_index: int
    title: str
    content: str
    source: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def split_documents(
    documents: Iterable[Mapping[str, Any]],
    *,
    chunk_size_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
) -> list[ChunkedDocument]:
    chunks: list[ChunkedDocument] = []
    for document in documents:
        chunks.extend(
            split_document(
                document,
                chunk_size_chars=chunk_size_chars,
                chunk_overlap_chars=chunk_overlap_chars,
            )
        )
    return chunks


def split_document(
    document: Mapping[str, Any],
    *,
    chunk_size_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
) -> list[ChunkedDocument]:
    if chunk_size_chars < 200:
        raise ValueError("chunk_size_chars must be at least 200")
    if chunk_overlap_chars < 0 or chunk_overlap_chars >= chunk_size_chars:
        raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")
    if not isinstance(document, Mapping):
        raise ValueError("document must be a mapping")

    metadata = document.get("metadata") if isinstance(document.get("metadata"), Mapping) else {}
    title = clean_text(document.get("title"))
    content = clean_text(document.get("content"))
    source = clean_text(document.get("source") or metadata.get("source"))
    if source not in SOURCE_TYPES:
        raise ValueError(f"invalid document source: {source!r}")
    if not title:
        raise ValueError("document title is required")
    if not content:
        raise ValueError("document content is required")

    document_id = clean_text(metadata.get("source_id")) or _stable_id(
        source,
        clean_text(document.get("url") or metadata.get("url")),
        title,
        content[:240],
    )
    content_chunks = _chunk_text(content, chunk_size_chars, chunk_overlap_chars)

    chunks: list[ChunkedDocument] = []
    for index, chunk_content in enumerate(content_chunks):
        chunk_id = _stable_id(document_id, str(index), chunk_content[:120])
        chunk_metadata = dict(metadata)
        chunk_metadata.update(
            {
                "chunk_id": chunk_id,
                "chunk_index": index,
                "document_id": document_id,
                "document_title": title,
                "source": source,
                "char_start_approx": _approx_start(content, chunk_content),
                "char_length": len(chunk_content),
            }
        )
        chunks.append(
            ChunkedDocument(
                chunk_id=chunk_id,
                document_id=document_id,
                chunk_index=index,
                title=title,
                content=chunk_content,
                source=source,
                metadata=chunk_metadata,
            )
        )
    return chunks


def _chunk_text(text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
    if len(text) <= chunk_size_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for segment in _segments(text):
        if len(segment) > chunk_size_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_fixed_windows(segment, chunk_size_chars, chunk_overlap_chars))
            continue

        candidate = f"{current} {segment}".strip() if current else segment
        if len(candidate) <= chunk_size_chars:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
        overlap = _tail_overlap(current, chunk_overlap_chars)
        current = f"{overlap} {segment}".strip() if overlap else segment

    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def _segments(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?。！？])\s+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _fixed_windows(text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    step = chunk_size_chars - chunk_overlap_chars
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size_chars >= len(text):
            break
        start += step
    return chunks


def _tail_overlap(text: str, chunk_overlap_chars: int) -> str:
    if not text or chunk_overlap_chars == 0:
        return ""
    tail = text[-chunk_overlap_chars:]
    if " " in tail:
        tail = tail[tail.find(" ") + 1 :]
    return tail.strip()


def _approx_start(content: str, chunk_content: str) -> int:
    start = content.find(chunk_content[:80])
    return max(start, 0)


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:32]
