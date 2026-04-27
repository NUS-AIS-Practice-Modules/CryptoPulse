# Decisions Log

## 2026-04-19 - Codex Harness Naming

- Replace `CLAUDE.md` with `AGENTS.md`
- Replace `claude-progress.md` with `progress.md`
- Add `session-handoff.md` for continuity

Reason:

- The repository is being initialized for Codex workflows, not Claude Code workflows

## 2026-04-19 - Frontend Stack Preservation

- Keep the frontend module aligned with the owner's React + TypeScript + Tailwind + Vite proposal

Reason:

- Existing owner materials are already concrete
- The repo-level Ant Design preference remains the default for future frontend work unless a module doc already specifies another stack

## 2026-04-19 - Shared RAG Source Expansion

- Extend `DocumentSource` to include `news`

Reason:

- The RAG design depends on scheduled ingestion of news content in addition to whitepapers, regulatory docs, market data, case studies, and social media

## 2026-04-19 - Mock-First Default

- All consumer modules should assume `USE_MOCK=true` until provider interfaces are integration-ready

Reason:

- This preserves parallel development and reduces blocking between module owners

## 2026-04-26 - RAG Hybrid Retrieval Default

- Use Milvus native hybrid search as the preferred RAG retrieval path
- Store dense `embedding` and BM25-derived `sparse_vector` in the same Milvus collection
- Index dense vectors with `AUTOINDEX` and sparse vectors with `SPARSE_INVERTED_INDEX`
- Query with `AnnSearchRequest` plus `WeightedRanker`
- Keep the original dense Milvus + external BM25 + RRF implementation as a compatibility and debugging fallback

Reason:

- This matches the Milvus v2.6 official hybrid-search tutorial and the user's local Milvus v2.6.14 deployment
- It reduces application-layer coordination between a Milvus dense index and a separate BM25 JSON index
- It keeps source filtering and dense/sparse fusion inside Milvus, while preserving the old path for isolated BM25 checks
- Current full-corpus verification on `cryptopulse_rag_hybrid_bge_m3_bm25` returned Recall@5=1.0 on four benchmark queries

## 2026-04-27 - LoRA AutoDL Deployment Boundary

- Treat real LoRA inference as an external AutoDL service
- Keep the local Python interface stable: `predict_sentiment`, `batch_predict_sentiment`, and `generate_response`
- Route those functions to HTTP when `LORA_USE_MOCK=false` and `LORA_REMOTE_BASE_URL` is configured
- Keep deterministic mock/fallback behavior for local harness and mock-first E2E

Reason:

- The real LoRA model is deployed on AutoDL rather than as local model assets in this repository
- This lets Chatbot and Frontend integration continue without pretending local real-model inference is complete
- The eventual AutoDL integration only needs endpoint URL/auth configuration if the server implements the documented response shapes
