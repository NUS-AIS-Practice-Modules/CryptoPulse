# Decisions Log

## 2026-04-19 - Codex Harness Naming

- Replace `CLAUDE.md` with `AGENTS.md`
- Replace `claude-progress.md` with `progress.md`
- Add `session-handoff.md` for continuity

Reason:

- The repository is being initialized for Codex workflows, not Claude Code workflows

## 2026-04-19 - Frontend Stack Preservation

- Keep the frontend module aligned with the owner's React + TypeScript + Tailwind + Vite proposal

Reason:

- Existing owner materials are already concrete
- The repo-level Ant Design preference remains the default for future frontend work unless a module doc already specifies another stack

## 2026-04-19 - Shared RAG Source Expansion

- Extend `DocumentSource` to include `news`

Reason:

- The RAG design depends on scheduled ingestion of news content in addition to whitepapers, regulatory docs, market data, case studies, and social media

## 2026-04-19 - Mock-First Default

- All consumer modules should assume `USE_MOCK=true` until provider interfaces are integration-ready

Reason:

- This preserves parallel development and reduces blocking between module owners

