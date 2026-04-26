from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.ingestion.normalizer import SOURCE_TYPES

from .bm25 import build_bm25_index, sparse_vectors_for_chunks
from .chunker import ChunkedDocument, split_documents
from .embeddings import EmbeddingProvider, HashEmbeddingProvider, SentenceTransformerEmbeddingProvider
from .milvus_store import MilvusHybridVectorStore, MilvusSettings, MilvusVectorStore


class VectorStore(Protocol):
    def ensure_collection(self, dimension: int) -> None:
        ...

    def upsert(self, chunks: list[ChunkedDocument], vectors: list[list[float]]) -> int:
        ...


@dataclass(frozen=True)
class IndexingConfig:
    milvus_uri: str = "http://127.0.0.1:19530"
    milvus_token: str = ""
    collection_name: str = "cryptopulse_rag_chunks"
    embedding_model_name: str = "BAAI/bge-m3"
    chunk_size_chars: int = 1600
    chunk_overlap_chars: int = 240
    embedding_batch_size: int = 32
    vector_batch_size: int = 128
    embedding_dimension: int = 384
    use_mock_embeddings: bool = False
    processed_dir: str = "data/processed"
    bm25_index_path: str = "data/processed/bm25_index.json"
    chunks_path: str = "data/processed/chunks.jsonl"
    use_milvus_native_hybrid: bool = False

    @classmethod
    def from_env(cls) -> "IndexingConfig":
        return cls(
            milvus_uri=os.getenv("MILVUS_URI", cls.milvus_uri),
            milvus_token=os.getenv("MILVUS_TOKEN", cls.milvus_token),
            collection_name=os.getenv("MILVUS_COLLECTION", cls.collection_name),
            embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", cls.embedding_model_name),
            chunk_size_chars=int(os.getenv("RAG_CHUNK_SIZE_CHARS", cls.chunk_size_chars)),
            chunk_overlap_chars=int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", cls.chunk_overlap_chars)),
            embedding_batch_size=int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", cls.embedding_batch_size)),
            vector_batch_size=int(os.getenv("RAG_VECTOR_BATCH_SIZE", cls.vector_batch_size)),
            embedding_dimension=int(os.getenv("MOCK_EMBEDDING_DIMENSION", cls.embedding_dimension)),
            use_mock_embeddings=os.getenv("USE_MOCK_EMBEDDINGS", "false").lower()
            in {"1", "true", "yes"},
            processed_dir=os.getenv("PROCESSED_DATA_DIR", cls.processed_dir),
            bm25_index_path=os.getenv("BM25_INDEX_PATH", cls.bm25_index_path),
            chunks_path=os.getenv("RAG_CHUNKS_PATH", cls.chunks_path),
            use_milvus_native_hybrid=os.getenv("USE_MILVUS_NATIVE_HYBRID", "false").lower()
            in {"1", "true", "yes"},
        )


def load_normalized_documents(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        raise ValueError(f"input path does not exist: {input_path}")

    documents: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL on line {line_number}") from exc
    return documents


def index_documents(
    documents: list[dict[str, Any]],
    source: str,
    *,
    config: IndexingConfig | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStore | None = None,
    write_artifacts: bool = True,
) -> int:
    if source not in SOURCE_TYPES:
        raise ValueError(f"invalid source: {source!r}")
    if not documents:
        raise ValueError("documents are required")
    for document in documents:
        document_source = document.get("source") or source
        if document_source != source:
            raise ValueError("all documents must match the source argument")

    return index_corpus(
        [{**document, "source": source} for document in documents],
        config=config,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        write_artifacts=write_artifacts,
    )


def index_corpus(
    documents: list[dict[str, Any]],
    *,
    config: IndexingConfig | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStore | None = None,
    write_artifacts: bool = True,
) -> int:
    if not documents:
        raise ValueError("documents are required")
    config = config or IndexingConfig.from_env()
    chunks = split_documents(
        documents,
        chunk_size_chars=config.chunk_size_chars,
        chunk_overlap_chars=config.chunk_overlap_chars,
    )
    if not chunks:
        return 0

    embedding_provider = embedding_provider or _default_embedding_provider(config)
    vector_store = vector_store or _default_vector_store(config)
    vector_store.ensure_collection(embedding_provider.dimension)

    vectors: list[list[float]] = []
    for batch in _text_batches(chunks, config.embedding_batch_size):
        vectors.extend(embedding_provider.encode([_embedding_text(chunk) for chunk in batch]))

    bm25_index = build_bm25_index(chunks)
    if config.use_milvus_native_hybrid and isinstance(vector_store, MilvusHybridVectorStore):
        indexed_count = vector_store.upsert_hybrid(
            chunks,
            vectors,
            sparse_vectors_for_chunks(chunks, bm25_index),
        )
    else:
        indexed_count = vector_store.upsert(chunks, vectors)
    if write_artifacts:
        _write_chunks(chunks, config.chunks_path)
        bm25_index.save(config.bm25_index_path)
    return indexed_count


def _default_embedding_provider(config: IndexingConfig) -> EmbeddingProvider:
    if config.use_mock_embeddings:
        return HashEmbeddingProvider(config.embedding_dimension)
    return SentenceTransformerEmbeddingProvider(config.embedding_model_name)


def _default_vector_store(config: IndexingConfig) -> VectorStore:
    store_type = MilvusHybridVectorStore if config.use_milvus_native_hybrid else MilvusVectorStore
    return store_type(
        MilvusSettings(
            uri=config.milvus_uri,
            token=config.milvus_token,
            collection_name=config.collection_name,
            batch_size=config.vector_batch_size,
        )
    )


def _text_batches(chunks: list[ChunkedDocument], batch_size: int) -> list[list[ChunkedDocument]]:
    return [chunks[index : index + batch_size] for index in range(0, len(chunks), batch_size)]


def _embedding_text(chunk: ChunkedDocument) -> str:
    return f"{chunk.title}\n{chunk.content}"


def _write_chunks(chunks: list[ChunkedDocument], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
