# Frontend Module Architecture

## One-Line Summary

The Frontend module provides CryptoPulse's web UI and serves as the main entry point for user interaction, including chat Q&A, file upload, message display, and an optional dashboard for data visualization.

---

## Tech Stack

- **Framework**: React  
  Mature component model, well suited to building chat and dashboard pages, and lighter than Next.js for this project.

- **Language**: TypeScript  
  Improves interface safety and reduces API-field mistakes during team collaboration.

- **Styling**: Tailwind CSS  
  High development speed and a practical fit for rapid modern UI work.

- **State management**: React Context + Hooks  
  A lightweight approach that is sufficient for the current project size.

- **Charting library**: Recharts  
  Used for dashboard line and pie charts.

- **HTTP client**: Fetch API

- **Build tool**: Vite

---

## Page Structure

## Main Chat Page (Core Page)

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

Sidebar

- Chat page
- Dashboard page
- Settings (optional)

Chat Area

- Message list (user / AI messages)
- Input box
- File upload button
- Send button
- Loading state

---

## Dashboard Page (Optional)

Shows sentiment-analysis results:

- sentiment trend line chart
- Bullish / Bearish / Neutral distribution chart
- Top Topics
- summary data cards

---

## Backend Integration

### `POST /api/chat`

Used to:

- send user questions
- receive AI replies
- receive sentiment and source data

### `GET /api/sentiment/summary`

Used to:

- fetch dashboard trend data

### `GET /api/health`

Used to:

- check system status

---

## File Upload (Reserved)

Planned support:

- PDF
- TXT
- DOCX (later)

Used for:

- user-uploaded document Q&A
- RAG document analysis

## Key Design Decisions

| Decision | Choice | Reason |
| ---- | ------------ | ------------ |
| Frontend framework | React | Mature ecosystem and convenient component development |
| Type system | TypeScript | Type safety and fewer integration errors |
| Styling | Tailwind CSS | High development speed |
| State management | Context | Sufficient for the current project size |
| Charting library | Recharts | Easy React integration |
| Build tool | Vite | Fast startup and good DX |

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

- page presentation
- user interaction
- API calls
- frontend state management

Frontend is not responsible for:

- AI inference logic
- sentiment analysis algorithms
- RAG retrieval logic
- database storage
