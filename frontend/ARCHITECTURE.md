# Frontend Module Architecture

## One-Line Summary

The Frontend module provides CryptoPulse's web UI and serves as the user-facing entry point, including chat Q&A, file upload, message display, and an optional dashboard for data visualization.

## Tech Stack

- **Framework**: React
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State management**: React Context + Hooks
- **Charting library**: Recharts
- **HTTP client**: Fetch API
- **Build tool**: Vite

## Page Structure

### Main Chat Page

```text
┌────────────────────────────────────────┐
│ Header                                 │
├──────────────┬─────────────────────────┤
│ Sidebar      │ Chat Area               │
│ - Chat       │ Message list            │
│ - Dashboard  │ Input box               │
│ - Settings   │ Upload button + Send    │
└──────────────┴─────────────────────────┘
```

Sidebar:

- Chat page
- Dashboard page
- Settings (optional)

Chat Area:

- Message list (user messages / AI messages)
- Input box
- File upload button
- Send button
- Loading state

### Dashboard Page

- Sentiment trend line chart
- Bullish / Bearish / Neutral distribution chart
- Top Topics
- Data summary cards

## Backend Integration

- `POST /api/chat`
- `GET /api/sentiment/summary`
- `GET /api/health`

File upload is reserved for a later RAG document-analysis workflow and currently exists mainly as a UI placeholder.

## Key Design Decisions

| Decision | Choice | Reason |
|------|------|------|
| Frontend framework | React | Mature ecosystem and convenient component-based development |
| Type system | TypeScript | Safer interfaces and fewer integration errors |
| Styling | Tailwind CSS | High development speed |
| State management | Context + Hooks | Enough for the current project size |
| Charting library | Recharts | Integrates cleanly with React |
| Build tool | Vite | Fast startup and good local DX |

## Directory Layout

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ChatBox.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Sidebar.tsx
│   │   └── Charts.tsx
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   └── DashboardPage.tsx
│   ├── services/
│   │   └── api.ts
│   ├── hooks/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── vite.config.ts
```

## Module Boundaries

Frontend is responsible for:

- UI presentation
- user interaction
- API calls
- frontend state management

Frontend is not responsible for:

- AI inference logic
- sentiment analysis algorithms
- RAG retrieval logic
- database storage
