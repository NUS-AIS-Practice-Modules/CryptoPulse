# Interface Contracts

This file is the single source of truth for all cross-module interfaces. Update it before changing any shared contract.

## Interface Registry

| Interface | Provider | Consumer(s) | Status |
|-----------|----------|-------------|--------|
| Chatbot REST API | Chatbot | Frontend | defined |
| Sentiment inference | LoRA | Chatbot | defined |
| Response generation | LoRA | Chatbot | defined |
| Retrieval API | RAG | Chatbot | defined |
| NER extraction | Chatbot | Frontend response pipeline | defined |

## Shared Types

Shared backend types live in `shared/types.py`.

Important enums:

- `SentimentLabel`
- `EntityType`
- `DocumentSource`

Important dataclasses:

- `SentimentResult`
- `GenerationResult`
- `RetrievedDocument`
- `RetrievalResult`
- `Entity`
- `ChatMessage`
- `Conversation`

## Interface: Chatbot -> Frontend

### Overview

- Provider: `chatbot`
- Consumer: `frontend`
- Mechanism: REST API
- SLA: `POST /api/chat < 15s`, `GET /api/sentiment/summary < 1s` in normal development conditions

### Endpoint: `POST /api/chat`

Request:

```json
{
  "message": "What's the current sentiment on Bitcoin?",
  "conversation_id": "conv-abc123",
  "options": {
    "include_sentiment": true,
    "include_sources": true
  }
}
```

Response:

```json
{
  "reply": "Based on recent social media analysis, Bitcoin sentiment is currently bullish...",
  "sentiment": {
    "label": "Bullish",
    "confidence": 0.85,
    "breakdown": {
      "bullish": 0.85,
      "bearish": 0.1,
      "neutral": 0.05
    }
  },
  "entities": [
    { "text": "Bitcoin", "type": "CRYPTO", "start": 45, "end": 52, "confidence": 0.91 }
  ],
  "sources": [
    { "title": "Bitcoin Whitepaper", "relevance": 0.92, "snippet": "..." }
  ],
  "conversation_id": "conv-abc123",
  "timestamp": "2026-04-15T10:30:00Z"
}
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Empty or malformed request body | HTTP 422 |
| UpstreamUnavailable | LoRA or RAG unavailable in real mode | HTTP 503 |
| InternalError | Unexpected pipeline failure | HTTP 500 |

Mock behavior:

- With `USE_MOCK=true`, the endpoint returns a deterministic reply, synthetic sentiment payload, and stub sources

### Endpoint: `GET /api/sentiment/summary`

Request example:

```text
/api/sentiment/summary?crypto=BTC&period=7d
```

Response:

```json
{
  "crypto": "BTC",
  "period": "7d",
  "overall_sentiment": "Bullish",
  "trend": [
    { "date": "2026-04-09", "bullish": 0.65, "bearish": 0.2, "neutral": 0.15 }
  ],
  "top_topics": ["ETF approval", "Halving", "Institutional adoption"],
  "data_points_analyzed": 15234
}
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidPeriod | Unsupported `period` value | HTTP 422 |
| InternalError | Aggregation failure | HTTP 500 |

Mock behavior:

- Returns a fixed trend dataset for local dashboard development

### Endpoint: `GET /api/health`

Response:

```json
{
  "status": "ok",
  "modules": {
    "lora": { "status": "ok", "model_loaded": true },
    "rag": { "status": "ok", "documents_indexed": 9200 },
    "ner": { "status": "ok", "backend": "llm" }
  }
}
```

## Interface: LoRA -> Chatbot

### Overview

- Provider: `lora`
- Consumer: `chatbot`
- Mechanism: Python function call
- SLA: single inference calls should stay within interactive-chat tolerances for local development

### Function: `predict_sentiment`

```python
def predict_sentiment(text: str) -> SentimentResult:
    ...
```

Output:

```python
@dataclass
class SentimentResult:
    label: str
    confidence: float
    scores: dict[str, float]
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| ModelNotLoaded | Weights or runtime unavailable | raises `RuntimeError` |
| InvalidInput | Empty text input | raises `ValueError` |

Mock behavior:

- Returns a stable bullish or neutral fixture depending on input keywords

### Function: `generate_response`

```python
def generate_response(prompt: str, context: str = "", max_tokens: int = 512) -> GenerationResult:
    ...
```

Output:

```python
@dataclass
class GenerationResult:
    text: str
    model_name: str
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| ModelNotLoaded | Runtime unavailable | raises `RuntimeError` |
| InvalidInput | Empty prompt | raises `ValueError` |

Mock behavior:

- Returns deterministic stub text with a mock model name

### Function: `batch_predict_sentiment`

```python
def batch_predict_sentiment(texts: list[str]) -> list[SentimentResult]:
    ...
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Empty batch or malformed list | raises `ValueError` |
| ModelNotLoaded | Runtime unavailable | raises `RuntimeError` |

## Interface: RAG -> Chatbot

### Overview

- Provider: `rag`
- Consumer: `chatbot`
- Mechanism: Python function call
- SLA: `retrieve < 1.5s`, `get_context_for_llm < 3s` under documented module conditions

### Function: `retrieve`

```python
def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    ...
```

Output:

```python
@dataclass
class RetrievedDocument:
    title: str
    content: str
    source: str
    relevance_score: float
    metadata: dict


@dataclass
class RetrievalResult:
    query: str
    documents: list[RetrievedDocument]
    total_candidates: int
    retrieval_time_ms: float
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Empty query or invalid `top_k` | raises `ValueError` |
| BackendUnavailable | Vector store or index unavailable | raises `RuntimeError` |

Mock behavior:

- Returns a stable set of retrieved documents with fixed metadata fields

### Function: `get_context_for_llm`

```python
def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
    ...
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Empty query | raises `ValueError` |
| BackendUnavailable | Retrieval backend unavailable | raises `RuntimeError` |

Mock behavior:

- Returns a short formatted context string suitable for prompt assembly

### Function: `index_documents`

```python
def index_documents(documents: list[dict], source: str) -> int:
    ...
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Malformed documents or invalid source | raises `ValueError` |
| BackendUnavailable | Storage backend unavailable | raises `RuntimeError` |

## Interface: Chatbot Internal NER

### Function: `extract_entities`

```python
def extract_entities(text: str) -> list[Entity]:
    ...
```

Output:

```python
@dataclass
class Entity:
    text: str
    type: str
    start: int
    end: int
    confidence: float
```

Errors:

| Error | When | How signaled |
|-------|------|--------------|
| InvalidInput | Empty text | raises `ValueError` or returns empty list by module decision |
| BackendFailure | LLM or model backend fails | logged error, returns empty list where appropriate |

Mock behavior:

- In mock mode, entity extraction may use hardcoded fixtures or a simplified parser

