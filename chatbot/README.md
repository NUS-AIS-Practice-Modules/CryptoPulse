# CryptoPulse Chatbot Module

**Owner**: Wei Yitao (E1458658)  
**Module role**: System integration layer that combines NER, sentiment analysis, RAG, and LLM generation into a unified REST API service

---

## Module Architecture

```text
User message
    ↓
POST /api/chat
    ↓
1. NER entity extraction  → identify "Bitcoin" → BTC (normalized to ticker)
2. Sentiment cache lookup → lookup("BTC") → Bullish 60% / Bearish 25% / Neutral 15%
3. RAG knowledge retrieval → entity-augmented query → background knowledge text
4. Prompt assembly        → system role + RAG context + sentiment data + history + user message
5. LLM response generation → OpenAI gpt-4o-mini (or LoRA generate_response)
    ↓
Return reply + sentiment + entities + sources
```

### Dependencies

```text
Frontend ──HTTP──▶ Chatbot ──Python functions──▶ RAG (knowledge retrieval)
                           ──file read────────▶ LoRA-produced sentiment_summary.json
                           ──built-in────────▶ NER (LLM-based entity extraction)
```

---

## Quick Start

### 1. Environment Setup (First Time)

```bash
cd chatbot
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Start the Service (Mock Mode, No API Key Required)

```bash
USE_MOCK=true .venv/bin/uvicorn src.app:app --reload --port 8000
```

Successful startup looks like:

```text
INFO  Loading sentiment cache: 6 cryptos from ./data/sentiment_summary.json
INFO  Uvicorn running on http://0.0.0.0:8000
```

### 3. Start the Service (Real Mode)

Set the real key in `.env`:

```env
USE_MOCK=false
OPENAI_API_KEY=sk-your-key
```

Then run:

```bash
.venv/bin/uvicorn src.app:app --reload --port 8000
```

---

## API Endpoints

### `GET /api/health`

Checks the status of each submodule.

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "modules": {
    "lora": {"status": "mock", "model_loaded": false},
    "rag":  {"status": "mock", "documents_indexed": 0},
    "ner":  {"status": "ok",   "backend": "llm"}
  }
}
```

---

### `POST /api/chat`

Main conversation endpoint. It receives a user message, runs the full NLP pipeline, and returns the response.

**Request:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current Bitcoin outlook?",
    "conversation_id": "session-001",
    "options": {
      "include_sentiment": true,
      "include_sources": true
    }
  }'
```

| Field | Type | Description |
|------|------|------|
| `message` | string (required) | User question |
| `conversation_id` | string (optional) | Conversation ID; generated automatically if omitted for multi-turn chat |
| `options.include_sentiment` | bool | Whether to include sentiment data in the response, default `true` |
| `options.include_sources` | bool | Whether to include RAG sources, default `true` |

**Response:**

```json
{
  "reply": "Based on current market analysis, Bitcoin (BTC) sentiment is bullish...",
  "sentiment": {
    "label": "Bullish",
    "confidence": 0.60,
    "breakdown": {"bullish": 0.60, "bearish": 0.25, "neutral": 0.15}
  },
  "entities": [
    {"text": "BTC", "type": "CRYPTO", "start": 25, "end": 32, "confidence": 0.99}
  ],
  "sources": [
    {"title": "Bitcoin Whitepaper", "relevance": 0.92, "snippet": "..."},
    {"title": "CoinGecko Market Overview", "relevance": 0.85, "snippet": "..."}
  ],
  "conversation_id": "session-001",
  "timestamp": "2026-04-21T10:30:00Z"
}
```

**Multi-turn conversation example:**

```bash
# Turn 1
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Tell me about Bitcoin", "conversation_id": "my-session"}'

# Turn 2 (Chatbot remembers prior context, keeps up to 5 turns)
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What about Ethereum?", "conversation_id": "my-session"}'
```

---

### `GET /api/sentiment/summary`

Returns historical sentiment trends for a specified crypto, used by the frontend dashboard.

```bash
curl "http://localhost:8000/api/sentiment/summary?crypto=BTC&period=7d"
```

| Parameter | Allowed values |
|------|--------|
| `crypto` | BTC, ETH, SOL, and other tickers |
| `period` | `7d` / `30d` / `90d` |

```json
{
  "crypto": "BTC",
  "period": "7d",
  "overall_sentiment": "Bullish",
  "trend": [
    {"date": "2026-04-15", "bullish": 0.63, "bearish": 0.21, "neutral": 0.16},
    {"date": "2026-04-16", "bullish": 0.67, "bearish": 0.19, "neutral": 0.14}
  ],
  "top_topics": ["ETF approval", "Halving", "Institutional adoption"],
  "data_points_analyzed": 15234
}
```

---

## Internal Pipeline Details

### NER Entity Extraction

- **Mock mode**: keyword matching (`bitcoin` → `BTC`, `ethereum` → `ETH`, and so on)
- **Real mode**: calls OpenAI `gpt-4o-mini` in JSON mode and normalizes to ticker symbols
- `CRYPTO` entities are used for sentiment cache lookups and RAG query augmentation

### Sentiment Data Source

**No real-time sentiment inference runs here.** The LoRA team processes social media comments offline and outputs:

```text
chatbot/data/sentiment_summary.json
```

Format:

```json
{
  "BTC": {"overall": "Bullish", "bullish": 0.60, "bearish": 0.25, "neutral": 0.15, "sample_count": 15234},
  "ETH": {"overall": "Neutral", "bullish": 0.38, "bearish": 0.35, "neutral": 0.27, "sample_count": 8901}
}
```

Chatbot loads this file into memory at startup, so lookups are `O(1)`. **The LoRA team owns updates to this file.**

### RAG Retrieval

- Query = raw user message + ticker extracted by NER, for example `"Bitcoin outlook BTC"`
- Calls `get_context_for_llm()` from `rag/src/retrieval.py`
- Mock mode returns a fixed crypto background paragraph

### LLM Generation

| `LLM_BACKEND` | Call path |
|--------------|---------|
| `openai` (default) | OpenAI ChatCompletion API |
| `lora` | `generate_response()` from `lora/src/inference.py` |

---

## Environment Variables

| Variable | Default | Description |
|------|--------|------|
| `USE_MOCK` | `true` | `true` = use mock data everywhere, no API key required |
| `NER_BACKEND` | `llm` | `llm` = OpenAI NER, `model` = BERTweet (not implemented yet) |
| `LLM_BACKEND` | `openai` | `openai` or `lora` |
| `OPENAI_API_KEY` | — | OpenAI API key, required when `USE_MOCK=false` |
| `OPENAI_NER_MODEL` | `gpt-4o-mini` | Model used for NER |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Model used for chat generation |
| `MAX_HISTORY_TURNS` | `5` | Maximum history turns passed to the LLM |
| `SENTIMENT_DATA_PATH` | `./data/sentiment_summary.json` | Path to the sentiment data produced by the LoRA team |

---

## Run Tests

```bash
USE_MOCK=true .venv/bin/pytest tests/ -v
```

Expected output: `17 passed`

---

## Integration With Other Modules

### What Chatbot Needs From the LoRA Team

`chatbot/data/sentiment_summary.json`, in the format shown above under **Sentiment Data Source**.

### What Chatbot Needs From the RAG Team

Functions in `rag/src/retrieval.py` as defined in `docs/INTERFACES.md`:

```python
def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str: ...
def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult: ...
```

### How the Frontend Team Calls Chatbot

All interface schemas are defined in `docs/INTERFACES.md`. Chatbot API base URL: `http://localhost:8000`.

---

## Interactive Docs

After the service starts, open `http://localhost:8000/docs` to test all endpoints in the browser.
