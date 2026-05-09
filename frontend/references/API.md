# Frontend API Reference

This document is intended for `CryptoPulse` frontend integration work and is based on the current reference materials plus the implemented frontend code.

The frontend currently accesses the backend through environment variables:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=true
```

- `VITE_API_BASE_URL`: backend service base URL
- `VITE_USE_MOCK`: whether to use local mock data
- When `VITE_USE_MOCK=false`, the frontend calls the real backend APIs

---

## 1. API Overview

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/chat` | User sends a question and receives an AI reply, sentiment label, and sources |
| `GET` | `/api/sentiment/summary` | Dashboard fetches sentiment trends, distribution, and topic summaries |
| `GET` | `/api/health` | Checks system health status |

Default composition:

```text
{VITE_API_BASE_URL}{path}
```

Example:

```text
http://localhost:8000/api/chat
```

---

## 2. Common Conventions

### 2.1 Content-Type

The frontend currently supports two request modes:

- When `/api/chat` is sent without file upload, use `application/json`
- When `/api/chat` includes file upload, use `multipart/form-data`
- `GET` endpoints do not require a request body

### 2.2 Error Handling

The current frontend error behavior is:

- If the HTTP status code is not `2xx`
- the frontend reads the response body as text
- and displays that text directly as the error message

Because of that, the backend should ideally return clear plain-text errors, or human-readable error descriptions in JSON.

Recommended status codes:

| Status code | Meaning |
| --- | --- |
| `200` | Request succeeded |
| `400` | Invalid parameters |
| `413` | Uploaded file is too large |
| `415` | Unsupported file type |
| `500` | Internal server error |
| `503` | Model/service temporarily unavailable |

---

## 3. `POST /api/chat`

### 3.1 Purpose

Used for the main chat flow:

- send user questions
- support multi-turn conversations
- optionally upload a document
- return the AI reply
- return sentiment labels and cited sources

### 3.2 Request Format

#### Scenario A: Text-only conversation

`Content-Type: application/json`

Request body:

```json
{
  "message": "How is BTC market sentiment today?",
  "conversation_id": "conv-001"
}
```

Field descriptions:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | User question |
| `conversation_id` | `string` | No | Multi-turn conversation ID; can be omitted on the first turn |

#### Scenario B: With file upload

`Content-Type: multipart/form-data`

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | User question |
| `conversation_id` | `string` | No | Multi-turn conversation ID |
| `file` | `File` | No | Uploaded document |

File types currently supported by the frontend selector:

- `PDF`
- `TXT`
- `DOCX`

Notes:

- The upload UI is already implemented
- Real file parsing still depends on backend support
- If the backend does not support file upload yet, it can ignore `file` and process text only

### 3.3 Success Response

```json
{
  "reply": "Current market sentiment is cautiously optimistic, and ETF-related narratives are driving BTC discussion volume.",
  "conversation_id": "conv-001",
  "sentiment": "Bullish",
  "sources": [
    {
      "title": "Market Snapshot",
      "url": "https://example.com/market-snapshot"
    }
  ]
}
```

Field descriptions:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `reply` | `string` | Yes | AI reply text |
| `conversation_id` | `string` | Yes | Conversation ID used by the frontend to link turns |
| `sentiment` | `"Bullish" \| "Bearish" \| "Neutral"` | No | Sentiment result for the current question |
| `sources` | `SourceLink[]` | No | List of cited sources |

`SourceLink` shape:

```json
{
  "title": "Source title",
  "url": "https://example.com/source"
}
```

### 3.4 Suggested Failure Responses

Plain-text example:

```text
Invalid request: message is required.
```

Or JSON example:

```json
{
  "error": "Invalid request: message is required."
}
```

Notes:

- The frontend currently prefers reading failure bodies as text
- If the backend returns JSON, it should still be easy to convert into readable text

---

## 4. `GET /api/sentiment/summary`

### 4.1 Purpose

Used by the Dashboard page to display:

- sentiment trend line charts
- Bullish / Bearish / Neutral distribution
- Top Topics
- summary statistic cards

### 4.2 Request Parameters

The current frontend does not yet send query parameters here.

If time-range filtering is added later, a reasonable extension would be:

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `range` | `string` | No | For example `7d` / `30d` / `90d` |

Example:

```text
/api/sentiment/summary?range=7d
```

### 4.3 Success Response

```json
{
  "totalAnalyses": 284,
  "activeTopics": 12,
  "health": "Healthy",
  "lastUpdated": "2026-04-22 10:30",
  "trend": [
    {
      "date": "04-16",
      "bullish": 28,
      "bearish": 18,
      "neutral": 12
    }
  ],
  "distribution": [
    {
      "name": "Bullish",
      "value": 56
    },
    {
      "name": "Bearish",
      "value": 22
    },
    {
      "name": "Neutral",
      "value": 22
    }
  ],
  "topTopics": ["BTC ETF flows", "ETH staking", "Macro rates"]
}
```

Field descriptions:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `totalAnalyses` | `number` | Yes | Total number of analyzed items |
| `activeTopics` | `number` | Yes | Number of currently active topics |
| `health` | `"Healthy" \| "Warning" \| "Offline"` | Yes | Overall health marker |
| `lastUpdated` | `string` | Yes | Last update time |
| `trend` | `TrendPoint[]` | Yes | Trend chart data |
| `distribution` | `SentimentDistribution[]` | Yes | Sentiment distribution data |
| `topTopics` | `string[]` | Yes | Top topics |

`TrendPoint` shape:

```json
{
  "date": "04-16",
  "bullish": 28,
  "bearish": 18,
  "neutral": 12
}
```

`SentimentDistribution` shape:

```json
{
  "name": "Bullish",
  "value": 56
}
```

---

## 5. `GET /api/health`

### 5.1 Purpose

Used to detect system availability and show API health status in the Dashboard.

### 5.2 Success Response

```json
{
  "status": "ok",
  "message": "All systems operational."
}
```

Field descriptions:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `status` | `"ok" \| "degraded" \| "down"` | Yes | System status |
| `message` | `string` | Yes | Status description |

---

## 6. TypeScript Type Mapping

The frontend currently uses the following core types.

### 6.1 `ChatReply`

```ts
interface ChatReply {
  reply: string;
  conversation_id: string;
  sentiment?: "Bullish" | "Bearish" | "Neutral";
  sources?: SourceLink[];
}
```

### 6.2 `DashboardSummary`

```ts
interface DashboardSummary {
  totalAnalyses: number;
  activeTopics: number;
  health: "Healthy" | "Warning" | "Offline";
  lastUpdated: string;
  trend: TrendPoint[];
  distribution: SentimentDistribution[];
  topTopics: string[];
}
```

### 6.3 `HealthStatus`

```ts
interface HealthStatus {
  status: "ok" | "degraded" | "down";
  message: string;
}
```

---

## 7. Mock Mode

The frontend supports a local mock mode, which is useful when the backend is not ready.

Enable it with:

```env
VITE_USE_MOCK=true
```

Mock-covered endpoints:

- `POST /api/chat`
- `GET /api/sentiment/summary`
- `GET /api/health`

Disable it with:

```env
VITE_USE_MOCK=false
```

---

## 8. Suggested Future Extensions

Recommended backend capabilities to reserve:

1. `POST /api/chat` streaming output, such as `SSE` or `WebSocket`
2. `GET /api/sentiment/summary` with a `range` query parameter
3. Historical conversation APIs such as `GET /api/conversations`
4. Dedicated document upload/parsing endpoints such as `POST /api/files/upload`
