# RAG Module Architecture

## One-Line Summary

This RAG module is built around `Milvus + BAAI/bge-m3 + BM25 + reranker` for the cryptocurrency domain. It covers whitepapers, regulatory documents, research reports, historical cases, news, and social-media content, and provides controllable, explainable context enhancement for Chatbot.

## Tech Stack

| Component | Choice | Reason |
|------|------|------|
| Vector database | Milvus | Supports large-scale vector indexing, filtering, and persistence |
| Embedding model | `BAAI/bge-m3` | Works well across news, reports, QA, and mixed text types |
| Chunking strategy | Semantic-first with fixed-window fallback | Balances context integrity and retrieval efficiency |
| Sparse retrieval | BM25 weights + Milvus sparse vector | Covers exact-match scenarios and keeps dense/sparse retrieval inside one Milvus collection |
| Fusion strategy | Milvus `hybrid_search` + `WeightedRanker` | Matches the official Milvus v2.6 approach and reduces app-layer fusion overhead |
| Reranking | Lightweight cross-encoder reranker | Improves top-k relevance |

## Knowledge Sources

- `whitepaper`
- `regulatory`
- `market_data`
- `case_study`
- `social_media`
- `news`

## Retrieval Pipeline

```text
user query
   ↓
query normalize
   ↓
dense embedding + BM25 sparse vector
   ↓
Milvus hybrid_search(AnnSearchRequest + WeightedRanker)
   ↓
cross-encoder reranker
   ↓
top-k documents
   ↓
context assembly
   ↓
get_context_for_llm()
```

The original path, `dense Milvus search + external BM25 JSON index + RRF`, is still preserved for compatibility and debugging. Production defaults to Milvus native hybrid retrieval because it matches the official v2.6 tutorial, stores both `embedding` and `sparse_vector` in a single collection, uses `AUTOINDEX` and `SPARSE_INVERTED_INDEX`, and completes fusion in one query with `AnnSearchRequest` and `WeightedRanker`.

## Hybrid Retrieval Decision

Comparison:

| Option | Advantages | Cost | Current role |
|------|------|------|------|
| Original: Milvus dense + app-layer BM25 + RRF | Straightforward implementation; BM25 JSON can be inspected offline; easy to unit test and use as a fallback | Every query touches two backends and fuses in the application layer; BM25 files and Milvus collections must stay in sync; tuning only affects the RRF layer | Kept for compatibility, debugging, and fallback |
| Official: Milvus dense+sparse native hybrid | Matches the Milvus v2.6 tutorial; dense and sparse fields live in one collection; indexing, filtering, and fusion stay inside Milvus; `WeightedRanker` can directly tune sparse/dense weights | Requires sparse-vector generation during indexing; schema differs from dense-only collections, so a new hybrid collection is required | Default recommended approach |

Choice: the module defaults to the official Milvus native hybrid approach. The reason is practical: the module already depends on local Milvus standalone, the current full corpus is only 1961 chunks, and rebuilding a hybrid collection is cheap. Measured retrieval on four benchmark queries achieved Recall@5=`1.0`, and `source_filter` works across all six source categories. The original path remains available to reduce rollback risk and to support isolated BM25 validation.

## Module Boundaries

This module is responsible for:

- multi-source knowledge collection and cleaning
- document normalization, chunking, and metadata modeling
- embeddings and vector ingestion
- BM25 indexing
- hybrid retrieval and reranking
- context assembly
- retrieval evaluation and refresh jobs

This module is not responsible for:

- final answer generation
- frontend presentation
- sentiment classification
- online crawling inside the request path

## Public Interfaces

```python
def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    ...


def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
    ...


def index_documents(documents: list[dict], source: str) -> int:
    ...
```

Fixed fields on `RetrievedDocument.metadata`:

- `url`
- `published_at`
- `language`
- `source_id`
- `entity_tags`
- `ingested_at`

## Directory Layout

```text
rag/
├── src/
│   ├── ingestion/
│   ├── indexing/
│   ├── retrieval/
│   ├── evaluation/
│   └── jobs/
├── data/
├── vectordb/
├── requirements.txt
└── README.md
```
