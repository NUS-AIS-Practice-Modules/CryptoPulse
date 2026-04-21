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

## Environment Variables

Edit `.env` after copying:

```env
USE_MOCK=true
NER_BACKEND=llm
LLM_BACKEND=openai
OPENAI_API_KEY=sk-your-key-here    # only needed when USE_MOCK=false
OPENAI_NER_MODEL=gpt-4o-mini
OPENAI_CHAT_MODEL=gpt-4o-mini
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

Interactive docs: http://localhost:8000/docs

## Notes

- Never commit `.env` — only `.env.example`
- Keep `USE_MOCK=true` until RAG module is integration-ready
- Sentiment data (`data/sentiment_summary.json`) is produced by the LoRA team — do not edit manually
- See `README.md` for full pipeline documentation
