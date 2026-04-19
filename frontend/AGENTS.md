# Frontend Module AGENTS

Work only inside `frontend/` unless the task explicitly requires cross-module integration.

## Read Order

1. `frontend/ARCHITECTURE.md`
2. `frontend/FEATURES.md`
3. `frontend/feature_list.json`
4. `docs/INTERFACES.md` when API behavior matters

## Working Rules

- Keep the module aligned with the documented React + TypeScript + Tailwind plan unless the user asks to change the stack
- Follow repo-level usability standards; prefer sober enterprise UI patterns
- Treat Chatbot APIs as the source of truth for payload shapes
- Use mock data or `VITE_USE_MOCK=true` while backend work is incomplete

## Verification

- `npm install`
- `npm run dev`
- `npm run build`

