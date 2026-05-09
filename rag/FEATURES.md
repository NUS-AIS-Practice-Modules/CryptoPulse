# RAG Feature List

## Rules

- Work on one feature at a time
- A feature is complete only after verification passes
- Retrieval quality must be backed by quantitative metrics
- Interface signatures must stay consistent with the harness contract

## Features

### RAG-001: Corpus Collection and Normalization (priority: 1)

- **Description**: Collect whitepapers, regulatory files, market research reports, historical cases, news, and social-media content, and convert them into a standardized document format that can be indexed.
- **Verification**:
  - [ ] Cover all six source categories
  - [ ] Every document includes `title/content/source/url/published_at/metadata`
  - [ ] `metadata` contains the required fixed field set
  - [ ] Raw inputs are converted into a unified text format
  - [ ] Noise removal and deduplication are complete

### RAG-002: Chunking, Metadata Modeling, and Index Ingestion (priority: 2)

- **Description**: Run chunking, embeddings, and index ingestion.
- **Verification**:
  - [ ] Chunking logic runs successfully
  - [ ] `BAAI/bge-m3` loads correctly
  - [ ] Milvus collection creation succeeds
  - [ ] BM25 index creation succeeds
  - [ ] `index_documents()` returns the correct indexed count

### RAG-003: Dense Retrieval Implementation (priority: 3)

- **Description**: Implement semantic retrieval on top of the vector index.
- **Verification**:
  - [ ] Basic queries return relevant results
  - [ ] Queries like `FTX collapse` hit case-study or news results in Top-5
  - [ ] Raw dense retrieval latency stays below `< 1.5s`
  - [ ] Returned fields are complete

### RAG-004: BM25 Retrieval and Hybrid Fusion (priority: 4)

- **Description**: Implement BM25 and RRF fusion.
- **Verification**:
  - [ ] BM25 can run independently
  - [ ] `Recall@5 >= 0.75`
  - [ ] `source_filter` works for all six source categories

### RAG-005: Rerank and Chatbot Interface Wrapper (priority: 5)

- **Description**: Add the reranker and package the external interface.
- **Verification**:
  - [ ] `retrieve()` signature matches the contract
  - [ ] `get_context_for_llm()` signature matches the contract
  - [ ] Returned context can be inserted directly into prompts
  - [ ] `get_context_for_llm()` latency stays below `< 3s`

### RAG-006: Scheduled Refresh and Evaluation Optimization (priority: 6)

- **Description**: Implement scheduled refresh for news and social-media data, and run benchmark / RAGAS evaluation.
- **Verification**:
  - [ ] Refresh job runs successfully
  - [ ] Outputs Recall@K, latency, Faithfulness, and related metrics
  - [ ] `Generation Faithfulness >= 85%`
  - [ ] Refresh failures do not corrupt existing indexes
