from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .chunker import ChunkedDocument


@dataclass(frozen=True)
class MilvusSettings:
    uri: str = "http://127.0.0.1:19530"
    token: str = ""
    collection_name: str = "cryptopulse_rag_chunks"
    batch_size: int = 128


class MilvusVectorStore:
    def __init__(self, settings: MilvusSettings) -> None:
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise RuntimeError(
                "pymilvus is required for Milvus indexing; install rag/requirements.txt"
            ) from exc

        kwargs = {"uri": settings.uri}
        if settings.token:
            kwargs["token"] = settings.token
        self.client = MilvusClient(**kwargs)
        self.settings = settings

    def ensure_collection(self, dimension: int) -> None:
        try:
            exists = self.client.has_collection(self.settings.collection_name)
        except Exception as exc:
            raise RuntimeError(f"Milvus is unavailable at {self.settings.uri}") from exc
        if exists:
            return

        try:
            from pymilvus import DataType, MilvusClient
        except ImportError as exc:
            raise RuntimeError("pymilvus is required for Milvus schema creation") from exc

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=128)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dimension)
        schema.add_field("title", DataType.VARCHAR, max_length=1024)
        schema.add_field("content", DataType.VARCHAR, max_length=8192)
        schema.add_field("source", DataType.VARCHAR, max_length=64)
        schema.add_field("url", DataType.VARCHAR, max_length=2048)
        schema.add_field("published_at", DataType.VARCHAR, max_length=64)
        schema.add_field("language", DataType.VARCHAR, max_length=16)
        schema.add_field("source_id", DataType.VARCHAR, max_length=256)
        schema.add_field("metadata", DataType.JSON)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )
        self.client.create_collection(
            collection_name=self.settings.collection_name,
            schema=schema,
            index_params=index_params,
        )

    def upsert(self, chunks: list[ChunkedDocument], vectors: list[list[float]]) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        if not chunks:
            return 0

        count = 0
        for batch_chunks, batch_vectors in _batches(chunks, vectors, self.settings.batch_size):
            rows = [
                _row_from_chunk(chunk, vector)
                for chunk, vector in zip(batch_chunks, batch_vectors)
            ]
            if hasattr(self.client, "upsert"):
                self.client.upsert(collection_name=self.settings.collection_name, data=rows)
            else:
                self.client.insert(collection_name=self.settings.collection_name, data=rows)
            count += len(rows)
        if hasattr(self.client, "flush"):
            self.client.flush(collection_name=self.settings.collection_name)
        return count


class MilvusHybridVectorStore(MilvusVectorStore):
    def ensure_collection(self, dimension: int) -> None:
        try:
            exists = self.client.has_collection(self.settings.collection_name)
        except Exception as exc:
            raise RuntimeError(f"Milvus is unavailable at {self.settings.uri}") from exc
        if exists:
            return

        try:
            from pymilvus import DataType, MilvusClient
        except ImportError as exc:
            raise RuntimeError("pymilvus is required for Milvus schema creation") from exc

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=128)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dimension)
        schema.add_field("sparse_vector", DataType.SPARSE_FLOAT_VECTOR)
        schema.add_field("title", DataType.VARCHAR, max_length=1024)
        schema.add_field("content", DataType.VARCHAR, max_length=8192)
        schema.add_field("source", DataType.VARCHAR, max_length=64)
        schema.add_field("url", DataType.VARCHAR, max_length=2048)
        schema.add_field("published_at", DataType.VARCHAR, max_length=64)
        schema.add_field("language", DataType.VARCHAR, max_length=16)
        schema.add_field("source_id", DataType.VARCHAR, max_length=256)
        schema.add_field("metadata", DataType.JSON)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="IP",
        )
        index_params.add_index(
            field_name="sparse_vector",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="IP",
        )
        self.client.create_collection(
            collection_name=self.settings.collection_name,
            schema=schema,
            index_params=index_params,
        )

    def upsert_hybrid(
        self,
        chunks: list[ChunkedDocument],
        dense_vectors: list[list[float]],
        sparse_vectors: list[dict[int, float]],
    ) -> int:
        if not (len(chunks) == len(dense_vectors) == len(sparse_vectors)):
            raise ValueError("chunks, dense_vectors, and sparse_vectors must have the same length")
        if not chunks:
            return 0

        count = 0
        for start in range(0, len(chunks), self.settings.batch_size):
            rows = [
                {
                    **_row_from_chunk(chunk, dense_vector),
                    "sparse_vector": sparse_vector,
                }
                for chunk, dense_vector, sparse_vector in zip(
                    chunks[start : start + self.settings.batch_size],
                    dense_vectors[start : start + self.settings.batch_size],
                    sparse_vectors[start : start + self.settings.batch_size],
                )
            ]
            if hasattr(self.client, "upsert"):
                self.client.upsert(collection_name=self.settings.collection_name, data=rows)
            else:
                self.client.insert(collection_name=self.settings.collection_name, data=rows)
            count += len(rows)
        if hasattr(self.client, "flush"):
            self.client.flush(collection_name=self.settings.collection_name)
        return count


def _batches(
    chunks: list[ChunkedDocument],
    vectors: list[list[float]],
    batch_size: int,
) -> Iterable[tuple[list[ChunkedDocument], list[list[float]]]]:
    for start in range(0, len(chunks), batch_size):
        yield chunks[start : start + batch_size], vectors[start : start + batch_size]


def _row_from_chunk(chunk: ChunkedDocument, vector: list[float]) -> dict[str, Any]:
    return {
        "id": chunk.chunk_id,
        "embedding": vector,
        "title": chunk.title[:1024],
        "content": chunk.content[:8192],
        "source": chunk.source,
        "url": str(chunk.metadata.get("url", ""))[:2048],
        "published_at": str(chunk.metadata.get("published_at", ""))[:64],
        "language": str(chunk.metadata.get("language", ""))[:16],
        "source_id": str(chunk.metadata.get("source_id", chunk.document_id))[:256],
        "metadata": chunk.metadata,
    }
