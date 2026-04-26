import tempfile
import unittest
from pathlib import Path

from src.indexing import (
    BM25Index,
    HashEmbeddingProvider,
    IndexingConfig,
    build_bm25_index,
    index_documents,
    sparse_vector_for_text,
    sparse_vectors_for_chunks,
    split_document,
)


class MemoryVectorStore:
    def __init__(self) -> None:
        self.dimension = None
        self.rows = []

    def ensure_collection(self, dimension: int) -> None:
        self.dimension = dimension

    def upsert(self, chunks, vectors) -> int:
        self.rows.extend(zip(chunks, vectors))
        return len(chunks)


def document(source: str = "case_study", content: str | None = None) -> dict:
    return {
        "title": "FTX collapse case",
        "content": content
        or "FTX collapsed after liquidity stress. Customer assets and exchange controls failed. "
        * 40,
        "source": source,
        "url": "https://example.test/ftx",
        "published_at": "2026-04-20T00:00:00Z",
        "metadata": {
            "url": "https://example.test/ftx",
            "published_at": "2026-04-20T00:00:00Z",
            "language": "en",
            "source_id": "ftx-case",
            "entity_tags": ["FTX"],
            "ingested_at": "2026-04-25T00:00:00Z",
        },
    }


class IndexingTests(unittest.TestCase):
    def test_split_document_preserves_required_metadata(self) -> None:
        chunks = split_document(document(), chunk_size_chars=450, chunk_overlap_chars=80)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].document_id, "ftx-case")
        self.assertEqual(chunks[0].source, "case_study")
        self.assertIn("chunk_id", chunks[0].metadata)
        self.assertEqual(chunks[0].metadata["document_title"], "FTX collapse case")

    def test_build_bm25_index_can_search_terms(self) -> None:
        chunks = split_document(document(content="Bitcoin ETF flows expanded. FTX risk remained contained."))
        index = build_bm25_index(chunks)

        results = index.search("FTX risk", top_k=1)

        self.assertEqual(index.total_documents, 1)
        self.assertEqual(results[0]["chunk_id"], chunks[0].chunk_id)
        self.assertGreater(results[0]["score"], 0)

    def test_builds_sparse_vectors_for_milvus_native_hybrid(self) -> None:
        chunks = split_document(document(content="Aave V3 improves capital efficiency."))
        index = build_bm25_index(chunks)

        document_vectors = sparse_vectors_for_chunks(chunks, index)
        query_vector = sparse_vector_for_text(
            "Aave capital",
            document_frequencies=index.document_frequencies,
            total_documents=index.total_documents,
        )

        self.assertEqual(len(document_vectors), 1)
        self.assertTrue(document_vectors[0])
        self.assertTrue(query_vector)
        self.assertTrue(all(isinstance(key, int) for key in query_vector))

    def test_index_documents_returns_chunk_count_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            vector_store = MemoryVectorStore()
            config = IndexingConfig(
                chunk_size_chars=450,
                chunk_overlap_chars=80,
                embedding_batch_size=2,
                embedding_dimension=32,
                bm25_index_path=str(Path(tmp_dir) / "bm25.json"),
                chunks_path=str(Path(tmp_dir) / "chunks.jsonl"),
                use_mock_embeddings=True,
            )

            count = index_documents(
                [document()],
                "case_study",
                config=config,
                embedding_provider=HashEmbeddingProvider(32),
                vector_store=vector_store,
            )

            self.assertEqual(count, len(vector_store.rows))
            self.assertEqual(vector_store.dimension, 32)
            self.assertTrue(Path(config.bm25_index_path).exists())
            self.assertTrue(Path(config.chunks_path).exists())
            loaded = BM25Index.load(config.bm25_index_path)
            self.assertEqual(loaded.total_documents, count)

    def test_index_documents_rejects_mismatched_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "all documents must match"):
            index_documents(
                [document("news")],
                "case_study",
                embedding_provider=HashEmbeddingProvider(8),
                vector_store=MemoryVectorStore(),
                write_artifacts=False,
            )


if __name__ == "__main__":
    unittest.main()
