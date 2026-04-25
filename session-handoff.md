# Session Handoff

## Verified Now

- Root harness files exist
- Module doc sets exist for all four modules
- `init.sh` exists and is syntactically valid
- RAG-001 normalization layer passes local unit verification
- RAG-001 PDF import path produced 37 normalized documents from local PDFs and DOCX web links; web links use real report PDF downloads where exposed

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

## Broken Or Unverified

- Dependency installation paths are documented but not executed
- Remote push flow is unverified in this session
- RAG-001 real six-source corpus collection is not finished because social_media is still missing
- RAG-002 indexing, Milvus, embeddings, retrieval, reranking, and evaluation are not implemented yet

## Next Best Step

- Highest-priority unfinished feature: finish `RAG-001`
- Why it is next: five source categories are now imported; social_media still needs a documented/importable source
- What counts as passing: all six source categories have documented/importable raw inputs, normalization runs on them, and metadata/noise/dedupe evidence is recorded
- What must not change during that step: shared contracts unless the change is coordinated via `docs/INTERFACES.md`

## Commands

- Startup: `./init.sh`
- Validation: `bash -n init.sh`
- Repo overview: `git status --short`
- RAG tests: `cd rag && python -m unittest discover -s tests`
- RAG web PDF download: `cd rag && python -m src.ingestion.download_web_pdfs --links-docx /path/to/web-links.docx --output-dir data/raw/web_pdfs --manifest data/raw/web_pdf_manifest.jsonl`
- RAG PDF import: `cd rag && python -m src.ingestion.pdf_importer --manifest data/raw/combined_pdf_manifest.jsonl --output data/processed/normalized_documents.jsonl`
- RAG ingestion CLI: `cd rag && python -m src.ingestion.normalize_corpus --input data/raw/documents.json --output data/processed/normalized_documents.jsonl`
