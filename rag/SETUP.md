# RAG Module Setup

## Prerequisites

- Python >= 3.10
- pip >= 23
- Docker >= 24 (used to run local `Milvus standalone`)

## Installation

```bash
cd rag
python -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use the module-local `.venv`; do not install RAG dependencies into the conda
`base` environment. `--system-site-packages` is used here to reuse the local
PyTorch runtime without writing packages into `base`; packages installed by the
command above are written under `rag/.venv`.

## Start Local Milvus

```bash
wget https://github.com/milvus-io/milvus/releases/download/v2.6.14/milvus-standalone-docker-compose.yml -O docker-compose.yml
sudo docker compose up -d
```

Check container status:

```bash
docker ps
```

Expected standalone ports:

- Milvus gRPC: `127.0.0.1:19530`
- Milvus health/API: `127.0.0.1:9091`
- MinIO console/API: `127.0.0.1:9000-9001`

## Environment Variables

```bash
cp .env.example .env
```

`.env.example`:

```env
MILVUS_URI=http://127.0.0.1:19530
MILVUS_TOKEN=
MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25
EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181
RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base
USE_CROSS_ENCODER_RERANKER=false
USE_MILVUS_NATIVE_HYBRID=true
SPARSE_WEIGHT=0.7
DENSE_WEIGHT=1.0
BM25_INDEX_PATH=data/processed/bm25_index.json
RAW_DATA_DIR=./data/raw
PROCESSED_DATA_DIR=./data/processed
NEWS_REFRESH_CRON=0 */6 * * *
SOCIAL_REFRESH_CRON=0 */3 * * *
USE_MOCK=true
USE_MOCK_EMBEDDINGS=false
MOCK_EMBEDDING_DIMENSION=384
```

## Commands

```bash
python -m unittest discover -s tests
python -m src.ingestion.download_web_pdfs --links-docx /path/to/web-links.docx --output-dir data/raw/news --manifest data/raw/web_pdf_manifest.jsonl
python -m src.ingestion.pdf_importer --manifest data/raw/combined_pdf_manifest.jsonl --output data/processed/normalized_documents.jsonl
python -m src.ingestion.normalize_corpus --input data/raw/documents.json --output data/processed/normalized_documents.jsonl
python -m src.indexing.build_index --input data/processed/normalized_documents.jsonl
python -m src.indexing.build_index --input data/processed/normalized_documents.jsonl --mock-embeddings --mock-dimension 64 --collection cryptopulse_rag_chunks_mock64
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m src.indexing.build_index --input data/processed/normalized_documents.jsonl --milvus-native-hybrid --collection cryptopulse_rag_hybrid_bge_m3_bm25
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -c "from src.retrieval import retrieve; print(retrieve('What caused the FTX collapse?'))"
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -c "from src.retrieval import retrieve_dense, retrieve_bm25, retrieve_hybrid; print(retrieve_hybrid('Aave V3 capital efficiency'))"
python -m src.evaluation.benchmark
USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=true HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m src.evaluation.benchmark --top-k 5
USE_MILVUS_NATIVE_HYBRID=true USE_CROSS_ENCODER_RERANKER=true HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m src.evaluation.faithfulness --top-k 5 --min-score 0.85
python -m src.jobs.refresh_index --input data/processed/normalized_documents.jsonl --dry-run
python -m src.jobs.refresh_index
```

`build_index` reads normalized JSONL, splits documents into stable chunks,
writes `data/processed/chunks.jsonl`, writes a BM25 index to
`data/processed/bm25_index.json`, and upserts chunk vectors into Milvus. With
`--milvus-native-hybrid` or `USE_MILVUS_NATIVE_HYBRID=true`, the collection
stores both dense `embedding` and BM25-derived `sparse_vector` fields and uses
Milvus native `hybrid_search` at query time. Without that flag, the older dense
Milvus + external BM25 + RRF path remains available for compatibility checks.
The default embedding path loads `BAAI/bge-m3`; `--mock-embeddings` uses
deterministic local embeddings for Milvus and BM25 plumbing checks without a
model download.

For local offline BGE verification, point `EMBEDDING_MODEL_NAME` at the cached
snapshot path and run with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.

Retrieval entry points:

- `retrieve()` uses hybrid retrieval plus rerank; when `USE_MILVUS_NATIVE_HYBRID=true`, the base retrieval path is Milvus native hybrid search
- `retrieve_dense()` runs raw Milvus vector search
- `retrieve_bm25()` runs sparse BM25 search from `BM25_INDEX_PATH`
- `retrieve_hybrid()` runs Milvus native hybrid search when enabled, otherwise dense + BM25 RRF fusion
- `retrieve_reranked()` runs hybrid retrieval plus rerank; `retrieve()` points to this path

By default, reranking uses a local lexical reranker for deterministic development
latency. Set `USE_CROSS_ENCODER_RERANKER=true` and `RERANK_MODEL_NAME` to the
local `BAAI/bge-reranker-base` path or a Hugging Face model id to use the
CrossEncoder reranker.

Evaluation entry points:

- `python -m src.evaluation.benchmark --top-k 5` reports Recall@K and latency
- `python -m src.evaluation.faithfulness --top-k 5 --min-score 0.85` reports a grounded-answer lexical Faithfulness proxy
- `python -m src.jobs.refresh_index --dry-run` verifies refresh inputs without writing to Milvus

The Faithfulness command is intentionally a local proxy until the Chatbot
generation path is integrated. It checks whether predefined grounded answer
claims are supported by retrieved titles and content.

PDF import uses `pdftotext` first and falls back to `pdftoppm` + `tesseract`
OCR when extracted text is too short for indexing.

`download_web_pdfs` handles web report pages in this order:

1. accept cookie/consent prompts
2. prefer `USA` / `United States` for region prompts, then try `Spain` / `Spanish` if unavailable
3. save the real report PDF when a download/full-report link exists
4. fall back to browser-printed PDF only when no real report PDF is exposed

## Data Locations

- Raw corpus: `data/raw/{whitepaper,case_study,regulatory,market_data,news}/`
- Normalized and chunked artifacts: `data/processed/`
- Local vector storage: `vectordb/`
