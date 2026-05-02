# Session Handoff

## Verified Now

- Root harness files exist
- Module doc sets exist for all four modules
- `init.sh` exists and is syntactically valid
- RAG-001 normalization layer passes local unit verification
- RAG-001 PDF import path produced 44 normalized documents after the latest raw corpus refresh; web links use real report PDF downloads where exposed
- RAG-002 indexing layer passes local unit verification and mock embedding Milvus indexing against local Milvus
- Local BGE cache is usable from `rag/.venv`: offline load dimension `1024`, embedding shape `(1, 1024)`
- RAG-003 dense retrieval passes on a real BGE sample Milvus collection
- Full-corpus real BGE indexing and dense retrieval pass on collection `cryptopulse_rag_chunks_bge_m3_full`
- RAG-004 BM25 standalone retrieval and hybrid RRF pass
- RAG-005 rerank wrapper and Chatbot-facing retrieval/context functions pass with the default lexical reranker
- Local `BAAI/bge-reranker-base` cache is usable from `rag/.venv`
- Milvus native hybrid collection `cryptopulse_rag_hybrid_bge_m3_bm25` has 1961 rows and passes Recall@5=1.0 on the current four-query benchmark
- RAG-006 benchmark CLI, grounded-answer Faithfulness proxy, and refresh dry-run CLI pass initial verification
- Frontend builds successfully with `npm run build` after installing module-local npm dependencies
- Chatbot mock-mode tests pass from `chatbot/.venv`
- LoRA now has root-level harness docs and a minimal mock/fallback inference wrapper matching the shared interfaces
- Real LoRA inference is deployed on an external AutoDL OpenAI-compatible vLLM server and is verified through the local SSH tunnel
- Mock-first E2E passes with Frontend calling the local Chatbot REST API while Chatbot runs with `USE_MOCK=true`
- Chatbot isolated real-LoRA path passes with `USE_MOCK=false RAG_USE_MOCK=true LLM_BACKEND=lora LORA_USE_MOCK=false`
- Chatbot can import real RAG retrieval symbols from `rag.src.retrieval` after RAG package import fixes
- Chatbot `/api/health` now probes the configured Milvus collection and reports unavailable details instead of a fixed RAG document count
- Chatbot `/api/health` now probes AutoDL vLLM `/models` before reporting real LoRA as ok; missing tunnel/key/models degrade health instead of showing configuration-based ok
- Full no-mock E2E passes with one Chatbot process using real RAG and real AutoDL LoRA; latest script output was `full no-mock e2e ok`
- Frontend browser walkthrough passes against the full no-mock backend for Dashboard and Chat
- Frontend Settings displays current Vite runtime env, and Dashboard shows `Frontend Mode` so mock and real-api states are distinguishable

## Changed This Session

- Added Codex root routing and tracking files
- Added shared architecture, interfaces, data spec, and shared types
- Migrated module plans into module-local documentation
- Added `rag/src/ingestion/` normalizer and CLI
- Added DOCX link extraction, browser PDF download, real-report PDF detection, and PDF import utilities
- Added RAG ingestion unit tests
- Recorded RAG-001 partial evidence in `rag/feature_list.json` and `progress.md`
- Processed 18 DOCX web links into ignored local PDFs under `rag/data/raw/web_pdfs/` using 4 direct report PDFs and 14 cleaned browser-printed fallbacks
- Imported 19 provided local PDFs plus 18 rendered web PDFs into ignored `rag/data/processed/normalized_documents.jsonl`
- Rebuilt normalized corpus after seven problematic CoinShares PDFs were manually replaced in `rag/data/raw/web_pdfs/`
- Reclassified new root PDFs in `rag/data/raw/`, added OCR fallback for scanned PDFs, and rebuilt ignored `data/processed/normalized_documents.jsonl` to 44 documents
- Added `rag/src/indexing/` with chunking, BM25 index persistence, embedding providers, Milvus store adapter, and `build_index` CLI
- Indexed the 44 normalized documents into 1961 chunks with mock embeddings; generated ignored `data/processed/chunks.jsonl` and `data/processed/bm25_index.json`
- Updated `rag/SETUP.md` to use the Milvus v2.6.14 Docker Compose flow and module-local `.venv`
- Added `rag/src/retrieval/` with dense Milvus retrieval and `get_context_for_llm`
- Verified real BGE sample indexing: 2 normalized docs -> 83 chunks in `cryptopulse_rag_chunks_bge_m3_sample`
- Verified full real BGE indexing: 44 normalized docs -> 1961 chunks in `cryptopulse_rag_chunks_bge_m3_full`
- Added BM25 and hybrid RRF retrieval; public `retrieve()` now uses hybrid RRF, with `retrieve_dense()`, `retrieve_bm25()`, and `retrieve_hybrid()` also available
- Added `LexicalReranker`, optional `CrossEncoderReranker`, and `RerankingRetriever`; public `retrieve()` now runs hybrid + rerank
- Added Milvus native hybrid indexing/retrieval path using dense `embedding`, BM25-derived `sparse_vector`, `AUTOINDEX`, `SPARSE_INVERTED_INDEX`, `AnnSearchRequest`, and `WeightedRanker`
- Recorded the Milvus native hybrid vs external BM25 + RRF decision in `rag/ARCHITECTURE.md` and `docs/DECISIONS.md`
- Added RAG-006 `src.evaluation.benchmark`, `src.evaluation.faithfulness`, and `src.jobs.refresh_index` scaffolding
- Added `chatbot/.env.example`
- Updated Frontend API adapter to map Chatbot REST response shapes for chat, sentiment summary, and health
- Fixed Frontend TypeScript build references so `tsc -b` checks existing app sources
- Added LoRA root harness files: `AGENTS.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SETUP.md`, `requirements.txt`, and `feature_list.json`
- Added `lora/src/inference` mock/fallback wrappers and `lora/tests/test_inference.py`
- Replaced AutoDL custom endpoint placeholders with OpenAI-compatible vLLM `/chat/completions` calls
- Added AutoDL LoRA settings: `LORA_REMOTE_BASE_URL`, `LORA_REMOTE_API_KEY`, `LORA_REMOTE_TIMEOUT_SECONDS`, `LORA_SENTIMENT_MODEL`, and `LORA_CHAT_MODEL`
- Added Chatbot `RAG_USE_MOCK` isolation mode for real-LoRA testing without requiring local RAG/Milvus in the same service run
- Fixed LLM NER prompt brace escaping and added fallback keyword entities when OpenAI NER is unavailable
- Added reproducible mock-first E2E script at `scripts/verify_mock_first_e2e.py`
- Updated root, frontend, chatbot, and lora feature trackers with evidence from actual verification commands
- Added `scripts/verify_full_no_mock_e2e.py` for full real-provider verification
- Rewrote the root `README.md` with setup, Milvus, AutoDL tunnel, full no-mock startup, recording, verification, and troubleshooting instructions
- Updated `chatbot/SETUP.md` and `.env.example` with full no-mock RAG/LoRA environment variables
- Added `RAG_SYSTEM_SITE_PACKAGES` support so Chatbot can append the local system site-packages path after startup without shadowing Python stdlib modules
- Added `docs/DEMO_CHECKLIST.md` and updated the Frontend chat bubble to show `Sources` plus source snippets for recording
- Updated root and frontend trackers so milestone-006 and milestone-007 are passing after browser walkthrough evidence
- Fixed real/mock status consistency across Frontend and Chatbot health reporting

## Broken Or Unverified

- Remote push flow is unverified in this session
- RAG-001 real six-source corpus collection is not finished because social_media is still missing
- RAG-006 Faithfulness is currently a local lexical proxy; generation-based Faithfulness still needs Chatbot integration
- RAG-006 social refresh is not implemented because social_media is intentionally skipped
- Full no-mock API/script E2E is verified; browser-level walkthrough is verified; the remaining action is recording the video using the checklist
- The AutoDL API key must remain local-only; do not write it into tracked files
- AutoDL tunnel was restored on 2026-04-29 and verified through `/v1/models`
- Installing `rag/requirements.txt` into `chatbot/.venv` was blocked by sandbox network restrictions; current README documents a no-download fallback using the existing `rag/.venv` site-packages on `PYTHONPATH`
- A direct real RAG smoke process remained running during the latest attempt and Codex could not kill it because escalation quota was unavailable; check process `82305` if it is still present before retrying heavy RAG smoke

## Next Best Step

- Highest-priority unfinished feature: final video recording by the user
- Why it is next: code, docs, API E2E, and browser walkthrough are all verified
- What counts as passing: recording follows `docs/DEMO_CHECKLIST.md` and shows Dashboard health, range switching, Chat reply, sentiment, and RAG sources
- What must not change during that step: shared contracts unless the change is coordinated via `docs/INTERFACES.md`
- Immediate prerequisite: keep Milvus, AutoDL tunnel, Chatbot, and Frontend running during recording

## Commands

- Startup: `./init.sh`
- Validation: `bash -n init.sh`
- Repo overview: `git status --short`
- RAG tests: `cd rag && python -m unittest discover -s tests`
- RAG web PDF download: `cd rag && python -m src.ingestion.download_web_pdfs --links-docx /path/to/web-links.docx --output-dir data/raw/web_pdfs --manifest data/raw/web_pdf_manifest.jsonl`
- RAG PDF import: `cd rag && python -m src.ingestion.pdf_importer --manifest data/raw/combined_pdf_manifest.jsonl --output data/processed/normalized_documents.jsonl`
- RAG ingestion CLI: `cd rag && python -m src.ingestion.normalize_corpus --input data/raw/documents.json --output data/processed/normalized_documents.jsonl`
- RAG tests: `cd rag && python -m unittest discover -s tests`
- RAG mock Milvus index: `cd rag && python -m src.indexing.build_index --input data/processed/normalized_documents.jsonl --mock-embeddings --mock-dimension 64 --collection cryptopulse_rag_chunks_mock64`
- RAG venv tests: `cd rag && .venv/bin/python -m unittest discover -s tests`
- RAG real BGE sample retrieval: `cd rag && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MILVUS_COLLECTION=cryptopulse_rag_chunks_bge_m3_sample EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 .venv/bin/python -c "from src.retrieval import retrieve; print(retrieve('What does Aave V3 improve?', top_k=3))"`
- RAG full BGE hybrid retrieval: `cd rag && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MILVUS_COLLECTION=cryptopulse_rag_chunks_bge_m3_full EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 BM25_INDEX_PATH=data/processed/bm25_index.json .venv/bin/python -c "from src.retrieval import retrieve; print(retrieve('Aave V3 capital efficiency', top_k=3))"`
- RAG warmed context check: `cd rag && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MILVUS_COLLECTION=cryptopulse_rag_chunks_bge_m3_full EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 BM25_INDEX_PATH=data/processed/bm25_index.json .venv/bin/python -c "from src.retrieval import retrieve, get_context_for_llm; retrieve('warmup', top_k=1); print(get_context_for_llm('What does MiCA regulate in crypto assets?', max_tokens=800, top_k=3)[:500])"`
- RAG native hybrid benchmark: `cd rag && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=true MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base BM25_INDEX_PATH=data/processed/bm25_index.json .venv/bin/python -m src.evaluation.benchmark --top-k 5`
- RAG Faithfulness proxy: `cd rag && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=true MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base BM25_INDEX_PATH=data/processed/bm25_index.json .venv/bin/python -m src.evaluation.faithfulness --top-k 5 --min-score 0.85`
- RAG refresh dry-run: `cd rag && .venv/bin/python -m src.jobs.refresh_index --input data/processed/normalized_documents.jsonl --dry-run`
- Frontend install: `cd frontend && npm install`
- Frontend build: `cd frontend && npm run build`
- Chatbot install: `cd chatbot && python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- Chatbot tests: `cd chatbot && USE_MOCK=true .venv/bin/python -m pytest tests -q`
- LoRA install: `cd lora && python -m venv .venv && .venv/bin/pip install -r requirements.txt`
- LoRA compile: `cd lora && .venv/bin/python -m compileall src scripts`
- LoRA tests: `cd lora && .venv/bin/python -m pytest tests -q`
- Mock-first E2E services: `cd chatbot && USE_MOCK=true .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000`; `cd frontend && VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173`
- Mock-first E2E verification: `python scripts/verify_mock_first_e2e.py`
- AutoDL LoRA local wrapper check: `cd lora && LORA_USE_MOCK=false LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY .venv/bin/python -c "from src.inference import predict_sentiment; print(predict_sentiment('Bitcoin ETF approved'))"`
- Chatbot isolated real-LoRA check: `cd chatbot && USE_MOCK=false RAG_USE_MOCK=true LLM_BACKEND=lora LORA_USE_MOCK=false LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000`
- Chatbot full no-mock check: `cd chatbot && export RAG_SITE_PACKAGES=/Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/rag/.venv/lib/python3.11/site-packages && export PYTHONPATH="$RAG_SITE_PACKAGES:$PYTHONPATH" && USE_MOCK=false RAG_USE_MOCK=false LLM_BACKEND=lora LORA_USE_MOCK=false LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=false MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base BM25_INDEX_PATH=../rag/data/processed/bm25_index.json HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000`
- Full no-mock E2E verification: `python scripts/verify_full_no_mock_e2e.py`
