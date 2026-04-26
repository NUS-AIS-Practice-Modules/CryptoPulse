from __future__ import annotations

import argparse

from .embeddings import HashEmbeddingProvider
from .pipeline import IndexingConfig, index_corpus, load_normalized_documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Milvus and BM25 indexes for RAG.")
    parser.add_argument(
        "--input",
        default="data/processed/normalized_documents.jsonl",
        help="Normalized JSONL corpus path",
    )
    parser.add_argument("--milvus-uri", default=None, help="Milvus URI")
    parser.add_argument("--collection", default=None, help="Milvus collection name")
    parser.add_argument("--bm25-output", default=None, help="BM25 index JSON path")
    parser.add_argument("--chunks-output", default=None, help="Chunk JSONL output path")
    parser.add_argument("--mock-embeddings", action="store_true", help="Use deterministic local embeddings")
    parser.add_argument("--mock-dimension", type=int, default=384, help="Mock embedding dimension")
    parser.add_argument(
        "--milvus-native-hybrid",
        action="store_true",
        help="Store dense and sparse vectors in Milvus for native hybrid_search",
    )
    args = parser.parse_args(argv)

    base_config = IndexingConfig.from_env()
    config = IndexingConfig(
        **{
            **base_config.__dict__,
            "milvus_uri": args.milvus_uri or base_config.milvus_uri,
            "collection_name": args.collection or base_config.collection_name,
            "bm25_index_path": args.bm25_output or base_config.bm25_index_path,
            "chunks_path": args.chunks_output or base_config.chunks_path,
            "use_mock_embeddings": args.mock_embeddings or base_config.use_mock_embeddings,
            "embedding_dimension": args.mock_dimension,
            "use_milvus_native_hybrid": args.milvus_native_hybrid
            or base_config.use_milvus_native_hybrid,
        }
    )
    documents = load_normalized_documents(args.input)
    embedding_provider = HashEmbeddingProvider(args.mock_dimension) if args.mock_embeddings else None
    count = index_corpus(documents, config=config, embedding_provider=embedding_provider)
    print(f"indexed_chunks={count}")
    print(f"collection={config.collection_name}")
    print(f"bm25_index={config.bm25_index_path}")
    print(f"chunks={config.chunks_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
