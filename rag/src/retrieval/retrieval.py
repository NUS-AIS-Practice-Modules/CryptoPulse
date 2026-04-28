from __future__ import annotations

import os
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from ..indexing.bm25 import BM25Index, sparse_vector_for_text
from ..indexing.embeddings import EmbeddingProvider, HashEmbeddingProvider, SentenceTransformerEmbeddingProvider
from ..ingestion.normalizer import SOURCE_TYPES
from .rerank import CrossEncoderReranker, LexicalReranker, Reranker

try:
    from shared.types import RetrievedDocument, RetrievalResult
except ImportError:
    from dataclasses import dataclass as _dataclass

    @_dataclass
    class RetrievedDocument:
        title: str
        content: str
        source: str
        relevance_score: float
        metadata: dict

    @_dataclass
    class RetrievalResult:
        query: str
        documents: list[RetrievedDocument]
        total_candidates: int
        retrieval_time_ms: float


class VectorSearcher(Protocol):
    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        source_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class RetrievalConfig:
    milvus_uri: str = "http://127.0.0.1:19530"
    milvus_token: str = ""
    collection_name: str = "cryptopulse_rag_chunks"
    embedding_model_name: str = "BAAI/bge-m3"
    use_mock_embeddings: bool = False
    mock_embedding_dimension: int = 384
    bm25_index_path: str = "data/processed/bm25_index.json"
    rrf_k: int = 60
    rerank_model_name: str = "BAAI/bge-reranker-base"
    use_cross_encoder_reranker: bool = False
    use_milvus_native_hybrid: bool = False
    sparse_weight: float = 0.7
    dense_weight: float = 1.0

    @classmethod
    def from_env(cls) -> "RetrievalConfig":
        return cls(
            milvus_uri=os.getenv("MILVUS_URI", cls.milvus_uri),
            milvus_token=os.getenv("MILVUS_TOKEN", cls.milvus_token),
            collection_name=os.getenv("MILVUS_COLLECTION", cls.collection_name),
            embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", cls.embedding_model_name),
            use_mock_embeddings=os.getenv("USE_MOCK_EMBEDDINGS", "false").lower()
            in {"1", "true", "yes"},
            mock_embedding_dimension=int(os.getenv("MOCK_EMBEDDING_DIMENSION", cls.mock_embedding_dimension)),
            bm25_index_path=os.getenv("BM25_INDEX_PATH", cls.bm25_index_path),
            rrf_k=int(os.getenv("RRF_K", cls.rrf_k)),
            rerank_model_name=os.getenv("RERANK_MODEL_NAME", cls.rerank_model_name),
            use_cross_encoder_reranker=os.getenv("USE_CROSS_ENCODER_RERANKER", "false").lower()
            in {"1", "true", "yes"},
            use_milvus_native_hybrid=os.getenv("USE_MILVUS_NATIVE_HYBRID", "false").lower()
            in {"1", "true", "yes"},
            sparse_weight=float(os.getenv("SPARSE_WEIGHT", cls.sparse_weight)),
            dense_weight=float(os.getenv("DENSE_WEIGHT", cls.dense_weight)),
        )


class DenseRetriever:
    def __init__(
        self,
        *,
        config: RetrievalConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        vector_searcher: VectorSearcher | None = None,
    ) -> None:
        self.config = config or RetrievalConfig.from_env()
        self.embedding_provider = embedding_provider or _embedding_provider(self.config)
        self.vector_searcher = vector_searcher or MilvusVectorSearcher(self.config)

    def retrieve(self, query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
        _validate_query(query, top_k, source_filter)
        started = time.perf_counter()
        query_vector = self.embedding_provider.encode([query])[0]
        rows = self.vector_searcher.search(
            query_vector,
            top_k=top_k,
            source_filter=source_filter,
        )
        documents = [_document_from_row(row) for row in rows[:top_k]]
        return RetrievalResult(
            query=query,
            documents=documents,
            total_candidates=len(rows),
            retrieval_time_ms=(time.perf_counter() - started) * 1000,
        )


class BM25Retriever:
    def __init__(self, *, index_path: str | Path = "data/processed/bm25_index.json") -> None:
        self.index_path = Path(index_path)
        self.index = BM25Index.load(self.index_path)

    def retrieve(self, query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
        _validate_query(query, top_k, source_filter)
        started = time.perf_counter()
        rows = self.index.search(query, top_k=top_k, source_filter=source_filter)
        documents = [_document_from_bm25_row(row) for row in rows]
        return RetrievalResult(
            query=query,
            documents=documents,
            total_candidates=len(rows),
            retrieval_time_ms=(time.perf_counter() - started) * 1000,
        )


class HybridRetriever:
    def __init__(
        self,
        *,
        dense_retriever: DenseRetriever | None = None,
        bm25_retriever: BM25Retriever | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.config = config or RetrievalConfig.from_env()
        self.dense_retriever = dense_retriever or DenseRetriever(config=self.config)
        self.bm25_retriever = bm25_retriever or BM25Retriever(index_path=self.config.bm25_index_path)

    def retrieve(self, query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
        _validate_query(query, top_k, source_filter)
        started = time.perf_counter()
        candidate_k = max(top_k * 4, 20)
        dense = self.dense_retriever.retrieve(query, top_k=candidate_k, source_filter=source_filter)
        bm25 = self.bm25_retriever.retrieve(query, top_k=candidate_k, source_filter=source_filter)
        documents = _rrf_fuse(
            dense.documents,
            bm25.documents,
            top_k=top_k,
            rrf_k=self.config.rrf_k,
        )
        return RetrievalResult(
            query=query,
            documents=documents,
            total_candidates=len({ _document_key(document) for document in dense.documents + bm25.documents }),
            retrieval_time_ms=(time.perf_counter() - started) * 1000,
        )


class NativeMilvusHybridRetriever:
    def __init__(
        self,
        *,
        config: RetrievalConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        bm25_index: BM25Index | None = None,
        vector_searcher: "MilvusNativeHybridSearcher | None" = None,
    ) -> None:
        self.config = config or RetrievalConfig.from_env()
        self.embedding_provider = embedding_provider or _embedding_provider(self.config)
        self.bm25_index = bm25_index or BM25Index.load(self.config.bm25_index_path)
        self.vector_searcher = vector_searcher or MilvusNativeHybridSearcher(self.config)

    def retrieve(self, query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
        _validate_query(query, top_k, source_filter)
        started = time.perf_counter()
        dense_vector = self.embedding_provider.encode([query])[0]
        sparse_vector = sparse_vector_for_text(
            query,
            document_frequencies=self.bm25_index.document_frequencies,
            total_documents=self.bm25_index.total_documents,
        )
        rows = self.vector_searcher.search(
            dense_vector,
            sparse_vector,
            top_k=top_k,
            source_filter=source_filter,
        )
        return RetrievalResult(
            query=query,
            documents=[_document_from_row(row) for row in rows[:top_k]],
            total_candidates=len(rows),
            retrieval_time_ms=(time.perf_counter() - started) * 1000,
        )


class RerankingRetriever:
    def __init__(
        self,
        *,
        base_retriever: HybridRetriever | None = None,
        reranker: Reranker | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.config = config or RetrievalConfig.from_env()
        self.base_retriever = base_retriever or (
            NativeMilvusHybridRetriever(config=self.config)
            if self.config.use_milvus_native_hybrid
            else HybridRetriever(config=self.config)
        )
        self.reranker = reranker or _default_reranker(self.config)

    def retrieve(self, query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
        _validate_query(query, top_k, source_filter)
        started = time.perf_counter()
        candidate_k = max(top_k * 4, 20)
        candidates = self.base_retriever.retrieve(
            query,
            top_k=candidate_k,
            source_filter=source_filter,
        )
        documents = self.reranker.rerank(query, candidates.documents, top_k=top_k)
        return RetrievalResult(
            query=query,
            documents=documents,
            total_candidates=candidates.total_candidates,
            retrieval_time_ms=(time.perf_counter() - started) * 1000,
        )


class MilvusVectorSearcher:
    def __init__(self, config: RetrievalConfig) -> None:
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise RuntimeError("pymilvus is required for dense retrieval") from exc

        kwargs = {"uri": config.milvus_uri}
        if config.milvus_token:
            kwargs["token"] = config.milvus_token
        self.client = MilvusClient(**kwargs)
        self.collection_name = config.collection_name

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        source_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                anns_field="embedding",
                limit=top_k,
                filter=_source_expr(source_filter),
                output_fields=[
                    "title",
                    "content",
                    "source",
                    "url",
                    "published_at",
                    "language",
                    "source_id",
                    "metadata",
                ],
                search_params={"metric_type": "COSINE"},
            )
        except Exception as exc:
            raise RuntimeError(f"dense retrieval backend unavailable: {self.collection_name}") from exc
        return [_row_from_hit(hit) for hit in (results[0] if results else [])]


class MilvusNativeHybridSearcher:
    def __init__(self, config: RetrievalConfig) -> None:
        try:
            from pymilvus import MilvusClient, WeightedRanker
        except ImportError as exc:
            raise RuntimeError("pymilvus is required for native hybrid retrieval") from exc

        kwargs = {"uri": config.milvus_uri}
        if config.milvus_token:
            kwargs["token"] = config.milvus_token
        self.client = MilvusClient(**kwargs)
        self.collection_name = config.collection_name
        self.ranker = WeightedRanker(config.sparse_weight, config.dense_weight)

    def search(
        self,
        dense_vector: list[float],
        sparse_vector: dict[int, float],
        *,
        top_k: int,
        source_filter: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            from pymilvus import AnnSearchRequest

            expr = _source_expr(source_filter) or None
            dense_req = AnnSearchRequest(
                [dense_vector],
                "embedding",
                {"metric_type": "IP", "params": {}},
                limit=top_k,
                expr=expr,
            )
            sparse_req = AnnSearchRequest(
                [sparse_vector],
                "sparse_vector",
                {"metric_type": "IP", "params": {}},
                limit=top_k,
                expr=expr,
            )
            results = self.client.hybrid_search(
                collection_name=self.collection_name,
                reqs=[sparse_req, dense_req],
                ranker=self.ranker,
                limit=top_k,
                output_fields=[
                    "title",
                    "content",
                    "source",
                    "url",
                    "published_at",
                    "language",
                    "source_id",
                    "metadata",
                ],
            )
        except Exception as exc:
            raise RuntimeError(f"native hybrid retrieval backend unavailable: {self.collection_name}") from exc
        return [_row_from_hit(hit) for hit in (results[0] if results else [])]


def retrieve_dense(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    return _default_retriever().retrieve(query, top_k=top_k, source_filter=source_filter)


def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    return retrieve_reranked(query, top_k=top_k, source_filter=source_filter)


def retrieve_bm25(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    return _default_bm25_retriever().retrieve(query, top_k=top_k, source_filter=source_filter)


def retrieve_hybrid(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    config = RetrievalConfig.from_env()
    if config.use_milvus_native_hybrid:
        return _default_native_hybrid_retriever().retrieve(query, top_k=top_k, source_filter=source_filter)
    return _default_hybrid_retriever().retrieve(query, top_k=top_k, source_filter=source_filter)


def retrieve_reranked(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    return _default_reranking_retriever().retrieve(query, top_k=top_k, source_filter=source_filter)


def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    result = retrieve(query, top_k=top_k)
    budget_chars = max_tokens * 4
    sections: list[str] = []
    used = 0
    for index, document in enumerate(result.documents, start=1):
        snippet = f"[{index}] {document.title} ({document.source})\n{document.content}\n"
        if used + len(snippet) > budget_chars:
            snippet = snippet[: max(budget_chars - used, 0)]
        if snippet:
            sections.append(snippet)
            used += len(snippet)
        if used >= budget_chars:
            break
    return "\n".join(sections).strip()


@lru_cache(maxsize=1)
def _default_retriever() -> DenseRetriever:
    return DenseRetriever()


@lru_cache(maxsize=1)
def _default_bm25_retriever() -> BM25Retriever:
    return BM25Retriever(index_path=RetrievalConfig.from_env().bm25_index_path)


@lru_cache(maxsize=1)
def _default_hybrid_retriever() -> HybridRetriever:
    return HybridRetriever()


@lru_cache(maxsize=1)
def _default_native_hybrid_retriever() -> NativeMilvusHybridRetriever:
    return NativeMilvusHybridRetriever()


@lru_cache(maxsize=1)
def _default_reranking_retriever() -> RerankingRetriever:
    return RerankingRetriever()


def _embedding_provider(config: RetrievalConfig) -> EmbeddingProvider:
    if config.use_mock_embeddings:
        return HashEmbeddingProvider(config.mock_embedding_dimension)
    return SentenceTransformerEmbeddingProvider(config.embedding_model_name)


def _default_reranker(config: RetrievalConfig) -> Reranker:
    if config.use_cross_encoder_reranker:
        return CrossEncoderReranker(config.rerank_model_name)
    return LexicalReranker()


def _validate_query(query: str, top_k: int, source_filter: list[str] | None) -> None:
    if not query or not query.strip():
        raise ValueError("query is required")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    invalid_sources = set(source_filter or []) - SOURCE_TYPES
    if invalid_sources:
        raise ValueError(f"invalid source_filter values: {sorted(invalid_sources)}")


def _source_expr(source_filter: list[str] | None) -> str:
    if not source_filter:
        return ""
    values = ", ".join(f'"{source}"' for source in source_filter)
    return f"source in [{values}]"


def _row_from_hit(hit: Any) -> dict[str, Any]:
    if isinstance(hit, dict):
        entity = hit.get("entity", {})
        score = hit.get("distance", hit.get("score", 0.0))
        return {**entity, "score": float(score)}

    entity = getattr(hit, "entity", None) or {}
    score = getattr(hit, "distance", getattr(hit, "score", 0.0))
    return {**dict(entity), "score": float(score)}


def _document_from_row(row: dict[str, Any]) -> RetrievedDocument:
    metadata = dict(row.get("metadata") or {})
    for field in ("url", "published_at", "language", "source_id"):
        if field in row and field not in metadata:
            metadata[field] = row[field]
    return RetrievedDocument(
        title=str(row.get("title", "")),
        content=str(row.get("content", "")),
        source=str(row.get("source", "")),
        relevance_score=float(row.get("score", 0.0)),
        metadata=metadata,
    )


def _document_from_bm25_row(row: dict[str, Any]) -> RetrievedDocument:
    return RetrievedDocument(
        title=str(row.get("title", "")),
        content=str(row.get("content", "")),
        source=str(row.get("source", "")),
        relevance_score=float(row.get("score", 0.0)),
        metadata=dict(row.get("metadata") or {}),
    )


def _rrf_fuse(
    dense_documents: list[RetrievedDocument],
    bm25_documents: list[RetrievedDocument],
    *,
    top_k: int,
    rrf_k: int,
) -> list[RetrievedDocument]:
    scores: dict[str, float] = {}
    documents: dict[str, RetrievedDocument] = {}
    for ranking in (dense_documents, bm25_documents):
        for rank, document in enumerate(ranking, start=1):
            key = _document_key(document)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            if key not in documents:
                documents[key] = document

    fused = []
    for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]:
        document = documents[key]
        fused.append(
            RetrievedDocument(
                title=document.title,
                content=document.content,
                source=document.source,
                relevance_score=score,
                metadata=document.metadata,
            )
        )
    return fused


def _document_key(document: RetrievedDocument) -> str:
    metadata = document.metadata or {}
    return str(
        metadata.get("chunk_id")
        or f"{metadata.get('source_id', '')}|{document.title}|{document.content[:120]}"
    )
