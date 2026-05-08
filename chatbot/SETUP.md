# Chatbot Module Setup

## Prerequisites

- Python >= 3.10
- pip >= 23

GPU is not required for this module.

## Installation

```bash
cd chatbot
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

For full no-mock provider mode, Chatbot also needs the RAG runtime packages in
the same Python process. Preferred setup:

```bash
cd ..
chatbot/.venv/bin/pip install -r rag/requirements.txt
```

If local network policy blocks that install, start Chatbot with the existing
RAG venv's site-packages on `PYTHONPATH`:

```bash
export RAG_SITE_PACKAGES=/Users/kevinableyyyx/Desktop/AIS-Semester2/PLP/PLPpracticeModule/CryptoPulse/rag/.venv/lib/python3.11/site-packages
export PYTHONPATH="$RAG_SITE_PACKAGES:$PYTHONPATH"
export RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages
```

## Environment Variables

Edit `.env` after copying:

```env
USE_MOCK=true
RAG_USE_MOCK=false
NER_BACKEND=lora
LLM_BACKEND=openai
OPENAI_API_KEY=sk-your-key-here    # only needed when USE_MOCK=false
OPENAI_NER_MODEL=gpt-4o-mini
OPENAI_CHAT_MODEL=gpt-4o-mini
LORA_USE_MOCK=true
LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1
LORA_REMOTE_API_KEY=        # set locally; do not commit real keys
LORA_REMOTE_TIMEOUT_SECONDS=30
LORA_SENTIMENT_MODEL=sentiment-lora
LORA_CHAT_MODEL=ift-lora
MAX_HISTORY_TURNS=5
SENTIMENT_DATA_PATH=./data/sentiment_summary.json
HOST=0.0.0.0
PORT=8000
```

## Starting the Service

```bash
# Mock mode (no API key required)
USE_MOCK=true .venv/bin/uvicorn src.app:app --reload --port 8000

# Real mode (requires OPENAI_API_KEY and RAG module ready)
USE_MOCK=false .venv/bin/uvicorn src.app:app --reload --port 8000

# Isolated AutoDL LoRA mode (real LoRA intent/NER/chat/sentiment, mock RAG)
USE_MOCK=false RAG_USE_MOCK=true LLM_BACKEND=lora NER_BACKEND=lora LORA_USE_MOCK=false \
  LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
  LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY \
  .venv/bin/uvicorn src.app:app --reload --port 8000

# Full no-mock mode (real RAG, real AutoDL LoRA)
USE_MOCK=false RAG_USE_MOCK=false LLM_BACKEND=lora NER_BACKEND=lora LORA_USE_MOCK=false \
  LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
  LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY \
  USE_MILVUS_NATIVE_HYBRID=true \
  USE_CROSS_ENCODER_RERANKER=false \
  MILVUS_COLLECTION=cryptopulse_rag_hybrid_bge_m3_bm25 \
  EMBEDDING_MODEL_NAME=/Users/kevinableyyyx/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 \
  RERANK_MODEL_NAME=/Users/kevinableyyyx/.cache/modelscope/hub/models/BAAI/bge-reranker-base \
  BM25_INDEX_PATH=../rag/data/processed/bm25_index.json \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  RAG_SYSTEM_SITE_PACKAGES=/Users/kevinableyyyx/anaconda3/lib/python3.11/site-packages \
  .venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000
```

## Run Tests

```bash
USE_MOCK=true .venv/bin/pytest tests/ -v
```

## Verify the Service

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current sentiment on Bitcoin?", "conversation_id": "test-001"}'

curl "http://localhost:8000/api/sentiment/summary?crypto=BTC&period=7d"
```

Full no-mock E2E with Frontend running on `127.0.0.1:5173`:

```bash
cd ..
python scripts/verify_full_no_mock_e2e.py
```

Interactive docs: http://localhost:8000/docs

## Notes

- Never commit `.env` — only `.env.example`
- Use `RAG_USE_MOCK=true` only for isolated LoRA checks; full no-mock mode must keep `RAG_USE_MOCK=false`
- Sentiment data (`data/sentiment_summary.json`) is produced by the LoRA team — do not edit manually
- See `README.md` for full pipeline documentation
