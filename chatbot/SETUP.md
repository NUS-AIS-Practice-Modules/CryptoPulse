# Chatbot Module Setup

## Prerequisites

- Python >= 3.10
- pip >= 23

GPU is not required for the current integration phase.

## Installation

```bash
cd chatbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

```bash
cp .env.example .env
```

`.env.example`:

```env
USE_MOCK=true
NER_BACKEND=llm
LORA_MODEL_PATH=../lora/checkpoints/latest
RAG_DB_PATH=../rag/vectordb
NER_MODEL_PATH=./checkpoints/ner_latest
HOST=0.0.0.0
PORT=8000
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
```

## Starting the Service

```bash
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

## Verify the Service

```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current sentiment on Bitcoin?",
    "conversation_id": "test-001",
    "options": {"include_sentiment": true, "include_sources": true}
  }'
curl "http://localhost:8000/api/sentiment/summary?crypto=BTC&period=7d"
```

## Notes

- Commit `.env.example`, not `.env`
- Keep `USE_MOCK=true` until LoRA and RAG are integration-ready

