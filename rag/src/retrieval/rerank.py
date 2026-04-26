from __future__ import annotations

import re
from dataclasses import replace
from typing import Protocol

try:
    from shared.types import RetrievedDocument
except ImportError:
    from dataclasses import dataclass

    @dataclass
    class RetrievedDocument:
        title: str
        content: str
        source: str
        relevance_score: float
        metadata: dict


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.$%-]+")


class Reranker(Protocol):
    def rerank(self, query: str, documents: list[RetrievedDocument], *, top_k: int) -> list[RetrievedDocument]:
        ...


class LexicalReranker:
    def rerank(self, query: str, documents: list[RetrievedDocument], *, top_k: int) -> list[RetrievedDocument]:
        query_tokens = set(_tokens(query))
        scored = []
        for document in documents:
            text_tokens = set(_tokens(f"{document.title} {document.content}"))
            overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
            score = float(document.relevance_score) + overlap
            scored.append((score, document))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            replace(document, relevance_score=score)
            for score, document in scored[:top_k]
        ]


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError("sentence-transformers is required for CrossEncoder reranking") from exc
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[RetrievedDocument], *, top_k: int) -> list[RetrievedDocument]:
        if not documents:
            return []
        pairs = [(query, f"{document.title}\n{document.content}") for document in documents]
        scores = self.model.predict(pairs, show_progress_bar=False)
        scored = [
            (float(score), document)
            for score, document in zip(scores, documents)
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            replace(document, relevance_score=score)
            for score, document in scored[:top_k]
        ]


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
