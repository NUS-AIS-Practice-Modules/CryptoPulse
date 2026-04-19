# Data Specification

## Shared Conventions

- Time values use ISO 8601 strings in UTC unless a module explicitly documents otherwise
- Confidence and relevance scores use `0.0` to `1.0`
- `conversation_id` is an opaque string generated client-side or server-side and reused for multi-turn chat
- Shared Python-facing shapes are defined in `shared/types.py`

## Chat API Payloads

### `POST /api/chat`

Request body:

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

Response body fields:

- `reply`: assistant text
- `sentiment`: sentiment label, confidence, and score breakdown
- `entities`: extracted entities with character offsets
- `sources`: retrieval citations suitable for UI display
- `conversation_id`: same conversation identifier
- `timestamp`: response creation time

### `GET /api/sentiment/summary`

Query params:

- `crypto`: target asset symbol or alias
- `period`: one of `7d`, `30d`, `90d`

Response fields:

- `crypto`
- `period`
- `overall_sentiment`
- `trend`
- `top_topics`
- `data_points_analyzed`

## RAG Document Normalization

Every normalized document should contain:

- `title`
- `content`
- `source`
- `url`
- `published_at`
- `metadata`

`metadata` should include at least:

- `url`
- `published_at`
- `language`
- `source_id`
- `entity_tags`
- `ingested_at`

## Environment Variable Rules

- Commit `.env.example`, not `.env`
- Frontend uses `.env.example` -> `.env.local`
- Python modules use `.env.example` -> `.env`
- `USE_MOCK=true` is the safe default until providers are integration-ready

