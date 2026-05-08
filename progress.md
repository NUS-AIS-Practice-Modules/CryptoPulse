# Session Progress Log

## Current State

**Last Updated:** 2026-05-08
**Active Feature:** LoRA-IFT intent routing

## Status

### What's Done

- [x] Target repository cloned locally via SSH
- [x] Root Codex harness files initialized
- [x] Module document skeletons and trackers created
- [x] Cross-module interface contract drafted
- [x] RAG-001 normalization layer implemented with fixture coverage, metadata validation, cleanup, dedupe, JSON/JSONL IO, and CLI entry point
- [x] RAG-001 PDF corpus import path implemented: DOCX link extraction, cookie/region handling, real-report PDF download detection, browser PDF fallback, PDF text extraction, and normalized JSONL output
- [x] RAG-002 indexing layer implemented: chunking, metadata propagation, BM25 index persistence, Milvus collection/upsert adapter, and `build_index` CLI
- [x] RAG-002 verified against local Docker Compose Milvus and local BGE cache from module-local `rag/.venv`
- [x] RAG-003 dense retrieval interface implemented with Milvus search and context assembly
- [x] RAG-003 full-corpus dense retrieval verified against full real BGE Milvus collection
- [x] RAG-004 BM25 standalone retrieval and hybrid RRF fusion implemented and verified
- [x] RAG-005 rerank wrapper and Chatbot-facing retrieval/context functions implemented and verified
- [x] RAG hybrid retrieval decision recorded: Milvus native hybrid search is now the preferred path, with the original external BM25 + RRF path retained as fallback
- [x] RAG-006 initial benchmark, Faithfulness proxy, and refresh scaffolding implemented
- [x] LoRA module brought into the root harness layout with `AGENTS.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SETUP.md`, `requirements.txt`, and `feature_list.json`
- [x] LoRA mock/fallback Chatbot-facing wrappers added for `predict_sentiment`, `batch_predict_sentiment`, and `generate_response`
- [x] Frontend API adapter aligned with the documented Chatbot REST shapes for `/api/chat`, `/api/sentiment/summary`, and `/api/health`
- [x] Chatbot `.env.example` added so module setup matches `SETUP.md`
- [x] Mock-first E2E verification script added at `scripts/verify_mock_first_e2e.py`
- [x] AutoDL LoRA deployment decision recorded: the real LoRA model lives on an external AutoDL server, and local wrappers now expose `LORA_REMOTE_BASE_URL` hooks for later HTTP integration
- [x] AutoDL LoRA OpenAI-compatible vLLM integration implemented and verified through the local SSH tunnel
- [x] Chatbot `USE_MOCK=false RAG_USE_MOCK=true LLM_BACKEND=lora` isolated path verified with AutoDL LoRA and mock RAG
- [x] Full no-mock preparation added: RAG imports are package-compatible inside the Chatbot process, `/api/health` probes the configured Milvus collection, `scripts/verify_full_no_mock_e2e.py` exists, and the root `README.md` now documents Milvus, AutoDL tunnel, Chatbot, Frontend, and recording flow
- [x] Full no-mock E2E passed with one Chatbot process using real RAG and real AutoDL LoRA. `python scripts/verify_full_no_mock_e2e.py` returned `full no-mock e2e ok`, RAG health reported `documents_indexed=1961` for `cryptopulse_rag_hybrid_bge_m3_bm25`, `/api/chat` returned sentiment label `Neutral`, and 5 real RAG sources.
- [x] Frontend browser walkthrough passed against the full no-mock backend. Dashboard showed `ok · lora: ok, rag: ok, ner: ok`, the `90 Days` range refreshed real data, and Chat displayed a real answer with `Sentiment: Neutral`, non-empty conversation id, `Sources`, source titles, and snippets.
- [x] Added `docs/DEMO_CHECKLIST.md` with startup order, recording script, expected evidence, non-blocking gaps, and troubleshooting.
- [x] Fixed real/mock status consistency. Frontend Settings now reads current Vite runtime env, Dashboard shows `Frontend Mode`, and Chatbot health now probes AutoDL vLLM `/models` before reporting real LoRA as ok.
- [x] Added LoRA-IFT intent routing. LoRA now exposes `classify_intent()` through the existing AutoDL vLLM wrapper using `ift-lora`, and Chatbot routes intent classification through LoRA when `LLM_BACKEND=lora` while preserving the OpenAI path.

### What's In Progress

- [ ] Finish RAG-001 social_media corpus coverage
  - Details: 44 documents are normalized across whitepaper, regulatory, market_data, case_study, and news; social_media is still missing
  - Blockers: temporarily skipped by user instruction so RAG-002 can proceed
- [ ] Finish RAG-006 refresh/evaluation work
  - Details: benchmark CLI, grounded-answer Faithfulness proxy, and refresh dry-run CLI are implemented; native hybrid + CrossEncoder benchmark passes against local Milvus
  - Blockers: social refresh still depends on the temporarily skipped social_media source; real generation Faithfulness depends on Chatbot integration
- [x] Finish frontend browser walkthrough and demo recording readiness
  - Details: API-level full no-mock E2E passes, Frontend dev shell is reachable, and browser walkthrough validates Dashboard plus Chat for recording
  - Blockers: none known for the demo path; social_media corpus coverage remains intentionally skipped

### What's Next

1. Decide refresh behavior for news with current PDF/web corpus
2. Replace the local Faithfulness proxy with generation-based Faithfulness after Chatbot integration is available
3. Add a documented/importable social_media source when available
4. Record the final video using `docs/DEMO_CHECKLIST.md`

## Blockers / Risks

- [ ] Private repository clone depends on valid local SSH access
- [ ] Provider module docs still require eventual code-level confirmation against real implementations
- [ ] Real corpus collection still needs a social_media source decision
- [ ] RAG-006 social refresh remains blocked by the intentionally skipped social_media source
- [ ] RAG-006 currently uses a local lexical Faithfulness proxy, not a generation-based evaluator
- [x] Mock-first E2E is verified, and full no-mock E2E is now verified at API/script level
- [x] Browser-level frontend walkthrough is verified against the full no-mock backend
- [x] AutoDL LoRA health no longer reports ok from configuration alone; unavailable tunnel/key/model states degrade `/api/health`
- [ ] AutoDL API key must stay local-only and must not be committed
- [ ] Current environment blocked `chatbot/.venv/bin/pip install -r rag/requirements.txt` through sandbox network restrictions; documented fallback is to export `PYTHONPATH` to the existing `rag/.venv` site-packages

## Decisions Made

- **Codex root harness naming**: Use `AGENTS.md`, `progress.md`, and `session-handoff.md`
  - Context: This repo is being initialized for Codex rather than Claude Code
  - Alternatives considered: preserving `CLAUDE.md` and `claude-progress.md`
- **Frontend stack preservation**: Keep the module's existing React + Tailwind plan
  - Context: Owner materials already committed to Tailwind
  - Alternatives considered: normalizing the module to Ant Design 6 immediately
- **RAG source expansion**: Include `news` in shared source enums
  - Context: RAG owner materials depend on it
  - Alternatives considered: forcing the RAG module to drop news from v1
- **RAG hybrid retrieval default**: Prefer Milvus native hybrid search over the original external BM25 + RRF pipeline
  - Context: The user requested comparison with the official Milvus hybrid-search tutorial; current local Milvus is v2.6.14
  - Alternatives considered: keep application-layer dense Milvus + BM25 JSON + RRF as the default
  - Reason: native hybrid stores dense and sparse vectors in one collection, keeps source filtering/fusion in Milvus, and passed full-corpus Recall@5=1.0; the original path remains as fallback and for isolated BM25 checks
- **Mock-first E2E acceptance for this integration pass**: Verify Frontend against Chatbot REST with Chatbot `USE_MOCK=true`
  - Context: main now contains all modules, but real LoRA inference is not wired and should not be misreported as complete
  - Alternatives considered: force full no-mock E2E immediately
  - Reason: mock-first validates the cross-module REST contract and UI adapter now, while preserving honest milestone status for real provider integration
- **LoRA deployment boundary**: Treat real LoRA inference as an external AutoDL service
  - Context: the real LoRA model is deployed on AutoDL rather than inside the local repository
  - Alternatives considered: require local model checkpoint loading before continuing integration
  - Reason: local modules can keep moving by preserving the Python interface and adding remote HTTP hooks while waiting for the AutoDL URL/auth details
- **LoRA remote protocol**: Use AutoDL's OpenAI-compatible vLLM `/chat/completions` API
  - Context: the tunnel returned models `llama3.1-8b-instruct`, `ift-lora`, and `sentiment-lora`; direct chat-completions calls succeeded
  - Alternatives considered: keep custom `/predict_sentiment` and `/generate_response` endpoints
  - Reason: the deployed server already provides OpenAI-compatible chat completions, so matching that protocol avoids an unnecessary gateway
- **LoRA-IFT intent routing**: Use `ift-lora` for Chatbot intent classification when `LLM_BACKEND=lora`
  - Context: `intent_service.py` previously called OpenAI directly even in LoRA backend mode
  - Alternatives considered: point OpenAI SDK config at AutoDL or call AutoDL directly from Chatbot
  - Reason: routing through the LoRA wrapper preserves module boundaries and keeps NER/OpenAI configuration separate from intent classification

## Evidence of Completion

- [x] Repository structure created
- [x] Interface contract draft written
- [x] Root tracker populated
- [x] RAG-001 normalization verified: `cd rag && python -m unittest discover -s tests` ran 6 tests successfully; `python -m src.ingestion.normalize_corpus --help` and `python -m compileall src tests` also passed
- [x] RAG-001 corpus import verified: 18 DOCX links processed with real report PDF priority (4 direct PDFs, 14 browser-printed fallbacks), 19 local PDFs imported, 37 normalized documents produced with complete required metadata. Source counts: case_study=6, market_data=6, news=18, regulatory=5, whitepaper=2.
- [x] 2026-04-26: Rebuilt normalized corpus after user replaced seven problematic CoinShares PDFs in `rag/data/raw/web_pdfs/`; audited the seven files for profile/cookie/personal-data contamination and found no flags.
- [x] 2026-04-26: Reclassified new root PDFs in `rag/data/raw/`, added OCR fallback for scanned PDFs, and rebuilt the normalized corpus to 44 documents. Source counts: case_study=7, market_data=8, news=18, regulatory=6, whitepaper=5.
- [x] 2026-04-26: RAG-002 unit verification passed with `cd rag && python -m unittest discover -s tests` (10 tests). Mock embedding Milvus indexing passed against local Milvus from outside the sandbox: `indexed_chunks=1961`, collection `cryptopulse_rag_chunks_mock64_flush`, `row_count=1961`, BM25 total documents `1961`, terms `19901`.
- [x] 2026-04-26: Created `rag/.venv` and installed compatible RAG dependencies there, without modifying conda base. Verified local BGE cache offline: dimension `1024`, embedding shape `(1, 1024)`.
- [x] 2026-04-26: Real BGE sample indexing passed: 2 normalized docs -> 83 chunks, collection `cryptopulse_rag_chunks_bge_m3_sample`, Milvus `row_count=83`.
- [x] 2026-04-26: RAG-003 dense retrieval passed on the real BGE sample collection: query `What does Aave V3 improve?` returned Aave chunks with `total_candidates=3` and `retrieval_time_ms=1442.88`.
- [x] 2026-04-26: Full real BGE indexing completed: 44 docs -> 1961 chunks, collection `cryptopulse_rag_chunks_bge_m3_full`, Milvus `row_count=1961`. Full-corpus dense retrieval returned relevant Aave, case_study, and regulatory results with latencies 544.24ms, 75.10ms, and 383.41ms.
- [x] 2026-04-26: RAG-004 passed. BM25 standalone retrieval returned relevant filtered results; hybrid RRF Recall@5=1.0 on 4 benchmark queries with latencies 784.86ms, 142.82ms, 312.65ms, and 330.69ms. `source_filter` verified for whitepaper, regulatory, market_data, case_study, news, and social_media.
- [x] 2026-04-26: RAG-005 passed. Added lexical rerank by default and optional CrossEncoder reranker path. `retrieve()` now runs hybrid + rerank; `get_context_for_llm` signature remains stable. Verified reranked Binance case-study retrieval in 604.53ms and warmed `get_context_for_llm` in 216.37ms.
- [x] 2026-04-26: Verified local `BAAI/bge-reranker-base` cache from `/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base`; offline CrossEncoder load and scoring succeeded. CrossEncoder + Milvus native hybrid retrieval completed in 2857.51ms, and warmed `get_context_for_llm` completed in 895.30ms.
- [x] 2026-04-26: RAG-004 native hybrid path passed. Collection `cryptopulse_rag_hybrid_bge_m3_bm25` stores `embedding` and `sparse_vector`, has `row_count=1961`, and native hybrid Recall@5=1.0 on Aave, MiCA, Binance, and CoinShares benchmark queries.
- [x] 2026-04-26: RAG-006 initial scaffolding passed. `cd rag && .venv/bin/python -m unittest discover -s tests` ran 19 tests successfully; `.venv/bin/python -m compileall src tests` passed; `.venv/bin/python -m src.jobs.refresh_index --input data/processed/normalized_documents.jsonl --dry-run` reported 44 docs across case_study=7, market_data=8, news=18, regulatory=6, whitepaper=5; native hybrid + CrossEncoder benchmark reported Recall@5=1.0, average retrieval time 1374.60ms, wall time 16550.28ms; grounded-answer Faithfulness proxy reported generation_faithfulness=1.0 and average retrieval time 1316.83ms.
- [x] 2026-04-27: Frontend dependencies installed in `frontend/` and `npm run build` passed. The build emitted one Vite chunk-size warning but completed successfully.
- [x] 2026-04-27: Chatbot module-local `chatbot/.venv` created, dependencies installed, and `USE_MOCK=true .venv/bin/python -m pytest tests -q` passed with 17 tests.
- [x] 2026-04-27: LoRA module-local `lora/.venv` created, minimal harness dependencies installed, `.venv/bin/python -m compileall src scripts` passed, shell syntax checks passed, and `.venv/bin/python -m pytest tests -q` passed with 4 tests.
- [x] 2026-04-27: RAG re-verification passed with `cd rag && .venv/bin/python -m unittest discover -s tests` (19 tests).
- [x] 2026-04-27: Mock-first E2E passed. Started Chatbot with `USE_MOCK=true .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000` and Frontend with `VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173`; `python scripts/verify_mock_first_e2e.py` returned `mock-first e2e ok`.
- [x] 2026-04-27: Added AutoDL remote LoRA interface placeholders. `lora/src/inference` can forward `predict_sentiment`, `batch_predict_sentiment`, and `generate_response` to `LORA_REMOTE_BASE_URL`; Chatbot `.env.example` and settings now include `LORA_REMOTE_BASE_URL`, `LORA_REMOTE_API_KEY`, and `LORA_REMOTE_TIMEOUT_SECONDS`.
- [x] 2026-04-28: Replaced the custom AutoDL endpoint placeholder with OpenAI-compatible vLLM `/chat/completions`. Direct real-mode LoRA verification through the local tunnel returned normalized Bullish sentiment with scores and non-empty `ift-lora` generation text.
- [x] 2026-04-28: Chatbot isolated real-LoRA verification passed with `USE_MOCK=false RAG_USE_MOCK=true LLM_BACKEND=lora LORA_USE_MOCK=false`; `/api/chat` returned AutoDL LoRA reply, Bullish sentiment, BTC entity via fallback NER, and mock RAG sources.
- [x] 2026-04-28: Regression checks passed after the LoRA/Chatbot integration changes: `cd lora && .venv/bin/python -m pytest tests -q` (7 passed) and `cd chatbot && USE_MOCK=true .venv/bin/python -m pytest tests -q` (18 passed).
- [x] 2026-04-28: Full no-mock implementation prep added `scripts/verify_full_no_mock_e2e.py`, package-compatible RAG imports for Chatbot, and Milvus collection probing in Chatbot health. `chatbot/.venv/bin/python -c "from rag.src.retrieval import retrieve, get_context_for_llm; ..."` and `cd rag && .venv/bin/python -c "from src.retrieval import retrieve, get_context_for_llm; ..."` both imported successfully after the RAG import fix.
- [x] 2026-04-28: Regression after full no-mock prep passed: `cd chatbot && USE_MOCK=true .venv/bin/python -m pytest tests -q` (19 passed), `cd lora && .venv/bin/python -m pytest tests -q` (7 passed), `cd frontend && npm run build` passed with the existing Vite chunk-size warning, `cd rag && .venv/bin/python -m unittest discover -s tests` (19 tests OK), `./init.sh` passed, JSON tracker validation passed, `git diff --check` passed, and secret-pattern search returned no tracked-file matches.
- [x] 2026-04-29: Full no-mock E2E passed after AutoDL vLLM was restored. Chatbot was started with `USE_MOCK=false RAG_USE_MOCK=false LLM_BACKEND=lora LORA_USE_MOCK=false`, RAG dependency paths were bridged through `PYTHONPATH` plus `RAG_SYSTEM_SITE_PACKAGES`, Frontend was started with `VITE_USE_MOCK=false`, and `python scripts/verify_full_no_mock_e2e.py` returned `full no-mock e2e ok`.
- [x] 2026-04-29: Frontend browser walkthrough passed. Dashboard loaded without undefined/error text, showed `ok · lora: ok, rag: ok, ner: ok`, and `90 Days` changed the selected range. Chat sent `Use recent crypto reports to explain the Bitcoin market outlook.` and displayed a real answer, `Sentiment: Neutral`, `Sources`, source titles, and source snippets.
- [x] 2026-04-29 final verification: `python scripts/verify_full_no_mock_e2e.py` passed before the final documentation-only edits, returning `full no-mock e2e ok` with RAG collection `cryptopulse_rag_hybrid_bge_m3_bm25`, `rag_documents_indexed=1961`, sentiment `Neutral`, and `source_count=5`. Fresh regression after the final UI/docs updates passed: Chatbot `19 passed`, Frontend `npm run build` passed with the known Vite chunk-size warning, RAG `19 tests OK`, LoRA `7 passed`, `./init.sh` passed, all feature trackers parsed as JSON, `git diff --check` passed, and secret-pattern search returned no tracked-file matches.
- [x] 2026-05-02: Real/mock environment status consistency fixed and verified. Chatbot health tests passed with `USE_MOCK=true .venv/bin/python -m pytest tests -q` (24 passed). Direct health invocation with `USE_MOCK=false RAG_USE_MOCK=true LORA_USE_MOCK=false` and unavailable local AutoDL access returned top-level `degraded` with `lora.status=unavailable`. Frontend `npm run build` passed, and a temporary Vite run with `VITE_USE_MOCK=false VITE_API_BASE_URL=http://127.0.0.1:8000` served transformed modules containing those exact runtime env values.
- [x] 2026-05-08: LoRA-IFT intent routing implemented and verified. `cd lora && .venv/bin/python -m pytest tests -q` passed with 10 tests, and `cd chatbot && USE_MOCK=true .venv/bin/python -m pytest tests -q` passed with 28 tests.
- [x] 2026-05-08: Full real-chain verification passed with AutoDL running. `python scripts/verify_full_no_mock_e2e.py` returned `full no-mock e2e ok`, RAG reported collection `cryptopulse_rag_hybrid_bge_m3_bm25` with `documents_indexed=1961`, and targeted intent probes confirmed BTC sentiment triggers sentiment/no RAG, Ethereum technology triggers RAG/no sentiment, and Hello triggers neither.
- [x] 2026-05-08: Fixed the five failed real routing matrix cases by adding deterministic intent policy overrides and broader NER fallback coverage for regulators, exchanges, and events. The requested 14-case real matrix passed 14/14 after restarting Chatbot with `OPENAI_API_KEY` from `chatbot/.env`; Chatbot tests passed with 30 tests and LoRA tests passed with 10 tests.

## Notes for Next Session

The project is demo-ready for the agreed scope. The next practical action is recording the final video with `docs/DEMO_CHECKLIST.md`. Non-blocking future work remains: add a real `social_media` corpus, implement RAG social refresh, preserve LoRA training/run evidence if required by the course report, and replace the local Faithfulness proxy with generation-based evaluation.
