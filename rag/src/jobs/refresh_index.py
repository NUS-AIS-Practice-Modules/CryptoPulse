from __future__ import annotations

import argparse
from collections import Counter

from ..indexing import IndexingConfig, index_corpus, load_normalized_documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh the RAG Milvus and BM25 indexes.")
    parser.add_argument("--input", default="data/processed/normalized_documents.jsonl")
    parser.add_argument("--collection", default=None)
    parser.add_argument("--mock-embeddings", action="store_true")
    parser.add_argument("--milvus-native-hybrid", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    documents = load_normalized_documents(args.input)
    counts = Counter(document.get("source", "") for document in documents)
    print(f"documents={len(documents)}")
    print("sources=" + ",".join(f"{source}:{count}" for source, count in sorted(counts.items())))
    if args.dry_run:
        print("refresh_status=dry_run")
        return 0

    base = IndexingConfig.from_env()
    config = IndexingConfig(
        **{
            **base.__dict__,
            "collection_name": args.collection or base.collection_name,
            "use_mock_embeddings": args.mock_embeddings or base.use_mock_embeddings,
            "use_milvus_native_hybrid": args.milvus_native_hybrid
            or base.use_milvus_native_hybrid,
        }
    )
    indexed_count = index_corpus(documents, config=config)
    print(f"indexed_chunks={indexed_count}")
    print("refresh_status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
