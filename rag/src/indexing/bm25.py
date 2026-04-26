from __future__ import annotations

import json
import math
import re
import hashlib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .chunker import ChunkedDocument


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.$%-]+")


@dataclass(frozen=True)
class BM25Index:
    documents: list[dict[str, Any]]
    document_frequencies: dict[str, int]
    average_document_length: float
    total_documents: int
    k1: float = 1.5
    b: float = 0.75

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BM25Index":
        return cls(
            documents=list(payload.get("documents", [])),
            document_frequencies=dict(payload.get("document_frequencies", {})),
            average_document_length=float(payload.get("average_document_length", 0.0)),
            total_documents=int(payload.get("total_documents", 0)),
            k1=float(payload.get("k1", 1.5)),
            b=float(payload.get("b", 0.75)),
        )

    def save(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "BM25Index":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def search(self, query: str, *, top_k: int = 5, source_filter: list[str] | None = None) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("query is required")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_tokens = tokenize(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        allowed_sources = set(source_filter or [])
        for document in self.documents:
            if allowed_sources and document.get("source") not in allowed_sources:
                continue
            score = self._score(query_tokens, document)
            if score > 0:
                scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                **document,
                "score": score,
            }
            for score, document in scored[:top_k]
        ]

    def _score(self, query_tokens: list[str], document: Mapping[str, Any]) -> float:
        token_counts = Counter(document.get("tokens", []))
        document_length = max(int(document.get("token_count", 0)), 1)
        score = 0.0
        for token in query_tokens:
            frequency = token_counts.get(token, 0)
            if frequency == 0:
                continue
            doc_frequency = self.document_frequencies.get(token, 0)
            idf = math.log(1 + (self.total_documents - doc_frequency + 0.5) / (doc_frequency + 0.5))
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * document_length / max(self.average_document_length, 1.0)
            )
            score += idf * (frequency * (self.k1 + 1)) / denominator
        return score


def build_bm25_index(chunks: Iterable[ChunkedDocument]) -> BM25Index:
    documents: list[dict[str, Any]] = []
    document_frequencies: Counter[str] = Counter()
    total_tokens = 0

    for chunk in chunks:
        tokens = tokenize(f"{chunk.title} {chunk.content}")
        token_count = len(tokens)
        total_tokens += token_count
        document_frequencies.update(set(tokens))
        documents.append(
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "title": chunk.title,
                "content": chunk.content,
                "source": chunk.source,
                "metadata": chunk.metadata,
                "tokens": tokens,
                "token_count": token_count,
            }
        )

    total_documents = len(documents)
    average_document_length = total_tokens / total_documents if total_documents else 0.0
    return BM25Index(
        documents=documents,
        document_frequencies=dict(document_frequencies),
        average_document_length=average_document_length,
        total_documents=total_documents,
    )


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def sparse_vector_for_text(
    text: str,
    *,
    document_frequencies: Mapping[str, int],
    total_documents: int,
) -> dict[int, float]:
    tokens = tokenize(text)
    counts = Counter(tokens)
    vector: dict[int, float] = {}
    for token, frequency in counts.items():
        doc_frequency = int(document_frequencies.get(token, 0))
        idf = math.log(1 + (total_documents - doc_frequency + 0.5) / (doc_frequency + 0.5))
        weight = float(frequency) * idf
        if weight > 0:
            vector[_token_id(token)] = weight
    return vector


def sparse_vectors_for_chunks(
    chunks: Iterable[ChunkedDocument],
    index: BM25Index,
) -> list[dict[int, float]]:
    return [
        sparse_vector_for_text(
            f"{chunk.title} {chunk.content}",
            document_frequencies=index.document_frequencies,
            total_documents=index.total_documents,
        )
        for chunk in chunks
    ]


def _token_id(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") & 0x7FFFFFFF
