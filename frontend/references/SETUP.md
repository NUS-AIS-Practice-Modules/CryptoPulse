# Frontend Setup

## Prerequisites

- Node.js >= 18
- npm >= 9

---

## Installation

```bash
cd frontend
npm install
```

## Local Development

```bash
npm run dev
```

Default address:

```text
http://localhost:5173
```

## Production Build

```bash
npm run build
```

## Environment Variables

Create `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=true
```

Notes:

- `VITE_API_BASE_URL`: backend API base URL
- `VITE_USE_MOCK`: whether to use local mock data

## Mock Development Mode

Use local mock data before the backend is ready:

- `/api/chat`
- `/api/sentiment/summary`
- `/api/health`

## Integration Steps

1. Start the backend API service
2. Update `.env.local` to set `VITE_USE_MOCK=false`
3. Start the frontend with `npm run dev`
4. Test the chat flow and the Dashboard page

## Current Limitations

- File upload endpoints still depend on backend support
- Historical session support still depends on backend support
- Streaming output can later be extended with SSE / WebSocket
