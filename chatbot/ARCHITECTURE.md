# Chatbot Module Architecture

## Overview

Serves as the system's integration layer and API service, combining Crypto-NER, LoRA sentiment analysis, and RAG knowledge retrieval to expose a unified REST API for the frontend.

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Web Framework | FastAPI | Native async support, auto-generated docs, request/response validation |
| NER (current) | LLM-based prompt extraction | No training data required, immediately usable |
| NER (later) | BERTweet + classification head | Fits Twitter-style crypto text |
| LLM Response Generation | Claude API / OpenAI API | Stable during development, replaceable later |
| Conversation History | In-memory Python dict | Zero dependencies for early development |
| Data Validation | Pydantic v2 | Strong FastAPI integration |

## Internal Architecture

```text
REST API Layer (FastAPI)
│
├── POST /api/chat              -> ChatService
├── GET  /api/sentiment/summary -> SentimentService
└── GET  /api/health            -> HealthService

ChatService
│
├── Crypto-NER
├── LoRA sentiment inference
├── RAG context retrieval
├── Prompt assembly
└── LLM response generation
```

## NER Module Design

`ner_service.py` routes by `NER_BACKEND`:

- `NER_BACKEND=llm` -> `llm_ner.py`
- `NER_BACKEND=model` -> `model_ner.py`

Shared signature:

```python
def extract_entities(text: str) -> list[Entity]:
    ...
```

## Exposed Interfaces

- `POST /api/chat`
- `GET /api/sentiment/summary`
- `GET /api/health`

## Dependencies on Other Modules

| Module | Call method | Functions |
|--------|-------------|-----------|
| LoRA | Python function call | `predict_sentiment()` |
| RAG | Python function call | `get_context_for_llm()`, `retrieve()` |

Before dependencies are ready, use `USE_MOCK=true`.

## Directory Structure

```text
chatbot/
├── src/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── memory/
│   ├── mock/
│   ├── ner/
│   └── prompts/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

