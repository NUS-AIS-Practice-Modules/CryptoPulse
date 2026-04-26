# Session Progress Log

## Current State

**Last Updated:** 2026-04-26 15:45
**Active Feature:** RAG-006 in progress

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

### What's In Progress

- [ ] Finish RAG-001 social_media corpus coverage
  - Details: 44 documents are normalized across whitepaper, regulatory, market_data, case_study, and news; social_media is still missing
  - Blockers: temporarily skipped by user instruction so RAG-002 can proceed
- [ ] Finish RAG-006 refresh/evaluation work
  - Details: benchmark CLI, grounded-answer Faithfulness proxy, and refresh dry-run CLI are implemented; native hybrid + CrossEncoder benchmark passes against local Milvus
  - Blockers: social refresh still depends on the temporarily skipped social_media source; real generation Faithfulness depends on Chatbot integration

### What's Next

1. Decide refresh behavior for news with current PDF/web corpus
2. Replace the local Faithfulness proxy with generation-based Faithfulness after Chatbot integration is available
3. Add a documented/importable social_media source when available

## Blockers / Risks

- [ ] Private repository clone depends on valid local SSH access
- [ ] Provider module docs still require eventual code-level confirmation against real implementations
- [ ] Real corpus collection still needs a social_media source decision
- [ ] RAG-006 social refresh remains blocked by the intentionally skipped social_media source
- [ ] RAG-006 currently uses a local lexical Faithfulness proxy, not a generation-based evaluator

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

## Notes for Next Session

Continue in `rag/` with RAG-006 refresh behavior and eventual generation-based Faithfulness integration. RAG-001 social_media remains a documented temporary skip per user instruction.
