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
- Route those functions to the AutoDL OpenAI-compatible vLLM `/chat/completions` API when `LORA_USE_MOCK=false` and `LORA_REMOTE_BASE_URL` is configured
- Use `sentiment-lora` for sentiment classification and `ift-lora` for response generation
- Keep deterministic mock/fallback behavior for local harness and mock-first E2E

Reason:

- The real LoRA model is deployed on AutoDL rather than as local model assets in this repository
- This lets Chatbot and Frontend integration continue without pretending local real-model inference is complete
- The verified AutoDL server exposes `llama3.1-8b-instruct`, `ift-lora`, and `sentiment-lora` through the local SSH tunnel at `127.0.0.1:6006`
- Real API keys stay in local shell or `.env` only; they are not committed to repository files

## 2026-04-28 - Full No-Mock Local Dependency Boundary

- Preferred full no-mock Chatbot setup installs `rag/requirements.txt` into `chatbot/.venv`
- If local network policy blocks that install, the documented local fallback is to add the existing `rag/.venv/lib/python3.11/site-packages` to `PYTHONPATH` only when starting Chatbot, and set `RAG_SYSTEM_SITE_PACKAGES` so Chatbot appends the local system site-packages path after startup
- Keep conda `base` untouched
- Keep RAG and LoRA public interfaces unchanged

Reason:

- Chatbot must call real RAG and real AutoDL LoRA inside one service process for the demo
- The current local environment blocked dependency installation into `chatbot/.venv`, but `rag/.venv` already contains the verified RAG runtime packages
- Using a temporary `PYTHONPATH` bridge is explicit, reversible, and does not write dependencies into `base`

## 2026-05-08 - LoRA-IFT Intent Routing

- Use `ift-lora` for Chatbot intent classification when `LLM_BACKEND=lora`
- Keep `sentiment-lora` dedicated to sentiment classification
- Route Chatbot through the LoRA Python wrapper instead of calling the AutoDL HTTP endpoint directly
- Preserve OpenAI intent classification for `LLM_BACKEND=openai`

Reason:

- Intent classification is a structured routing task and should share the same LoRA integration boundary as response generation
- Reusing the LoRA wrapper keeps Chatbot independent from AutoDL transport details
- Keeping OpenAI and LoRA backends explicit avoids coupling intent routing to the NER model configuration

## 2026-05-08 - LoRA-IFT NER Primary Path

- Use `ift-lora` for Chatbot NER when `NER_BACKEND=lora`
- Keep OpenAI NER as the first fallback
- Keep local keyword rules as the final fallback for demo-critical entities such as `SEC`, `CFTC`, `FTX Collapse`, `ETF Approval`, `Binance`, `Coinbase`, and `Kraken`
- Preserve `sentiment-lora` exclusively for sentiment classification

Reason:

- NER is a structured extraction task and can share the existing LoRA inference boundary with intent routing
- Routing through the LoRA Python wrapper keeps Chatbot independent from AutoDL HTTP details
- OpenAI remains useful as a reliability fallback without being required for the primary real LoRA demo path
