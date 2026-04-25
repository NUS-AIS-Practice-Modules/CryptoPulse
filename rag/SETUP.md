# RAG 模块环境搭建

## 前置要求

- Python >= 3.10
- pip >= 23
- Docker >= 24（用于本地启动 `Milvus standalone`）

## 安装步骤

```bash
cd rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动本地 Milvus

```bash
docker run -d \
  --name cryptopulse-milvus \
  -p 19530:19530 \
  -p 9091:9091 \
  -v $(pwd)/vectordb:/var/lib/milvus \
  milvusdb/milvus:v2.4.6 \
  milvus run standalone
```

检查容器状态：

```bash
docker ps
```

## 环境变量

```bash
cp .env.example .env
```

`.env.example`:

```env
MILVUS_URI=http://127.0.0.1:19530
MILVUS_TOKEN=
MILVUS_COLLECTION=cryptopulse_rag_chunks
EMBEDDING_MODEL_NAME=BAAI/bge-m3
RERANK_MODEL_NAME=BAAI/bge-reranker-base
RAW_DATA_DIR=./data/raw
PROCESSED_DATA_DIR=./data/processed
NEWS_REFRESH_CRON=0 */6 * * *
SOCIAL_REFRESH_CRON=0 */3 * * *
USE_MOCK=true
```

## 运行命令

```bash
python -m unittest discover -s tests
python -m src.ingestion.download_web_pdfs --links-docx /path/to/web-links.docx --output-dir data/raw/web_pdfs --manifest data/raw/web_pdf_manifest.jsonl
python -m src.ingestion.pdf_importer --manifest data/raw/combined_pdf_manifest.jsonl --output data/processed/normalized_documents.jsonl
python -m src.ingestion.normalize_corpus --input data/raw/documents.json --output data/processed/normalized_documents.jsonl
python -m src.indexing.build_index --raw-dir data/raw --full
python -c "from src.retrieval.retrieval import retrieve; print(retrieve('What caused the FTX collapse?'))"
python -m src.evaluation.benchmark
python -m src.evaluation.ragas_eval
python -m src.jobs.refresh_index
```

`download_web_pdfs` handles web report pages in this order:

1. accept cookie/consent prompts
2. prefer `USA` / `United States` for region prompts, then try `Spain` / `Spanish` if unavailable
3. save the real report PDF when a download/full-report link exists
4. fall back to browser-printed PDF only when no real report PDF is exposed

## 数据存放

- 原始语料：`data/raw/`
- 标准化与分块产物：`data/processed/`
- 本地向量存储目录：`vectordb/`
