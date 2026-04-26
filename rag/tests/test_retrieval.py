import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.indexing import BM25Index
from src.indexing import HashEmbeddingProvider
from src.retrieval import (
    BM25Retriever,
    DenseRetriever,
    HybridRetriever,
    LexicalReranker,
    RerankingRetriever,
    RetrievalConfig,
    get_context_for_llm,
)
from src.retrieval.retrieval import RetrievedDocument, RetrievalResult


class MemoryVectorSearcher:
    def __init__(self) -> None:
        self.last_filter = None

    def search(self, query_vector, *, top_k, source_filter=None):
        self.last_filter = source_filter
        return [
            {
                "title": "FTX collapse case",
                "content": "FTX collapsed after liquidity stress and failures in exchange controls.",
                "source": "case_study",
                "score": 0.91,
                "metadata": {
                    "url": "https://example.test/ftx",
                    "published_at": "2026-04-20T00:00:00Z",
                    "language": "en",
                    "source_id": "ftx-case",
                    "entity_tags": ["FTX"],
                    "ingested_at": "2026-04-25T00:00:00Z",
                },
            }
        ][:top_k]


class RetrievalTests(unittest.TestCase):
    def test_dense_retriever_returns_contract_shape(self) -> None:
        searcher = MemoryVectorSearcher()
        retriever = DenseRetriever(
            config=RetrievalConfig(use_mock_embeddings=True, mock_embedding_dimension=16),
            embedding_provider=HashEmbeddingProvider(16),
            vector_searcher=searcher,
        )

        result = retriever.retrieve("What caused the FTX collapse?", top_k=1, source_filter=["case_study"])

        self.assertEqual(result.query, "What caused the FTX collapse?")
        self.assertEqual(result.total_candidates, 1)
        self.assertGreaterEqual(result.retrieval_time_ms, 0)
        self.assertEqual(result.documents[0].title, "FTX collapse case")
        self.assertEqual(result.documents[0].metadata["source_id"], "ftx-case")
        self.assertEqual(searcher.last_filter, ["case_study"])

    def test_retriever_validates_inputs(self) -> None:
        retriever = DenseRetriever(
            config=RetrievalConfig(use_mock_embeddings=True),
            embedding_provider=HashEmbeddingProvider(8),
            vector_searcher=MemoryVectorSearcher(),
        )

        with self.assertRaisesRegex(ValueError, "query is required"):
            retriever.retrieve(" ")
        with self.assertRaisesRegex(ValueError, "top_k"):
            retriever.retrieve("bitcoin", top_k=0)
        with self.assertRaisesRegex(ValueError, "invalid source_filter"):
            retriever.retrieve("bitcoin", source_filter=["blog"])

    def test_context_assembly_uses_retrieved_documents(self) -> None:
        retriever = DenseRetriever(
            config=RetrievalConfig(use_mock_embeddings=True),
            embedding_provider=HashEmbeddingProvider(8),
            vector_searcher=MemoryVectorSearcher(),
        )

        from src.retrieval import retrieval as retrieval_module

        original = retrieval_module._default_reranking_retriever
        retrieval_module._default_reranking_retriever = lambda: retriever
        try:
            context = get_context_for_llm("FTX", max_tokens=60, top_k=1)
        finally:
            retrieval_module._default_reranking_retriever = original

        self.assertIn("FTX collapse case", context)
        self.assertIn("case_study", context)

    def test_bm25_retriever_runs_independently_with_source_filter(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "bm25.json"
            BM25Index(
                documents=[
                    {
                        "chunk_id": "a",
                        "document_id": "doc-a",
                        "title": "MiCA regulation",
                        "content": "MiCA regulates crypto asset service providers.",
                        "source": "regulatory",
                        "metadata": {"chunk_id": "a", "source_id": "mica"},
                        "tokens": ["mica", "regulates", "crypto", "asset"],
                        "token_count": 4,
                    },
                    {
                        "chunk_id": "b",
                        "document_id": "doc-b",
                        "title": "Market update",
                        "content": "Bitcoin ETF flows increased.",
                        "source": "market_data",
                        "metadata": {"chunk_id": "b", "source_id": "market"},
                        "tokens": ["bitcoin", "etf", "flows"],
                        "token_count": 3,
                    },
                ],
                document_frequencies={"mica": 1, "regulates": 1, "crypto": 1, "asset": 1},
                average_document_length=3.5,
                total_documents=2,
            ).save(index_path)

            result = BM25Retriever(index_path=index_path).retrieve(
                "MiCA crypto",
                top_k=1,
                source_filter=["regulatory"],
            )

            self.assertEqual(result.documents[0].title, "MiCA regulation")
            self.assertEqual(result.documents[0].source, "regulatory")

    def test_hybrid_retriever_fuses_dense_and_bm25_rankings(self) -> None:
        dense_doc = RetrievedDocument(
            title="Aave V3",
            content="Aave V3 improves capital efficiency.",
            source="whitepaper",
            relevance_score=0.8,
            metadata={"chunk_id": "dense-a"},
        )
        shared_doc = RetrievedDocument(
            title="FTX case",
            content="FTX collapsed after liquidity stress.",
            source="case_study",
            relevance_score=0.7,
            metadata={"chunk_id": "shared"},
        )
        bm25_doc = RetrievedDocument(
            title="FTX case",
            content="FTX collapsed after liquidity stress.",
            source="case_study",
            relevance_score=2.0,
            metadata={"chunk_id": "shared"},
        )

        class FakeRetriever:
            def __init__(self, documents):
                self.documents = documents

            def retrieve(self, query, top_k=5, source_filter=None):
                return RetrievalResult(query, self.documents[:top_k], len(self.documents), 1.0)

        retriever = HybridRetriever(
            config=RetrievalConfig(use_mock_embeddings=True, rrf_k=60),
            dense_retriever=FakeRetriever([dense_doc, shared_doc]),
            bm25_retriever=FakeRetriever([bm25_doc]),
        )

        result = retriever.retrieve("FTX liquidity", top_k=2)

        self.assertEqual(result.documents[0].metadata["chunk_id"], "shared")
        self.assertGreater(result.documents[0].relevance_score, result.documents[1].relevance_score)

    def test_reranking_retriever_applies_reranker(self) -> None:
        off_topic = RetrievedDocument(
            title="Market note",
            content="ETF flows increased.",
            source="market_data",
            relevance_score=0.3,
            metadata={"chunk_id": "market"},
        )
        on_topic = RetrievedDocument(
            title="FTX liquidity case",
            content="FTX collapsed after liquidity stress.",
            source="case_study",
            relevance_score=0.2,
            metadata={"chunk_id": "ftx"},
        )

        class FakeHybridRetriever:
            def retrieve(self, query, top_k=5, source_filter=None):
                return RetrievalResult(query, [off_topic, on_topic], 2, 1.0)

        retriever = RerankingRetriever(
            config=RetrievalConfig(use_mock_embeddings=True),
            base_retriever=FakeHybridRetriever(),
            reranker=LexicalReranker(),
        )

        result = retriever.retrieve("FTX liquidity stress", top_k=1)

        self.assertEqual(result.documents[0].metadata["chunk_id"], "ftx")


if __name__ == "__main__":
    unittest.main()
