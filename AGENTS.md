# AGENTS.md

CryptoPulse is a four-module team project. This file is the root routing guide for Codex sessions.

## Startup Workflow

Before writing code:

1. Confirm working directory with `pwd`
2. Read this file fully
3. Read `ARCHITECTURE.md`
4. Read `docs/INTERFACES.md`
5. Run `./init.sh` if the repo state is unknown or stale
6. Read root `feature_list.json`
7. Pick one module or one integration task
8. Read that module's `AGENTS.md`, `ARCHITECTURE.md`, and `feature_list.json`

## Module Routing

At session start, state the module or integration task you are handling.

- Frontend work -> `frontend/AGENTS.md`
- Chatbot work -> `chatbot/AGENTS.md`
- LoRA work -> `lora/AGENTS.md`
- RAG work -> `rag/AGENTS.md`
- Integration work -> stay here and read `docs/INTERFACES.md`, `docs/DATA_SPEC.md`, and `docs/DECISIONS.md`

## Team Rules

- One feature at a time
- Root `feature_list.json` tracks milestones, not module sub-features
- Each module tracks its own work in module `feature_list.json`
- No cross-module edits unless the task is explicitly integration-related
- Any interface change must update `docs/INTERFACES.md` first
- Mock-first development is allowed; mock-only completion is not
- Every completion claim needs concrete verification evidence

## Interface Change Protocol

1. Propose the change and identify provider and consumer
2. Update `docs/INTERFACES.md`
3. Update shared types in `shared/types.py` if needed
4. Update mocks alongside real implementations
5. Re-run provider and consumer verification

## Project-Specific Notes

- Frontend defaults should generally align with Ant Design 6 style and interaction patterns, unless a module document already commits to another concrete approach
- The current frontend module docs intentionally preserve a React + Tailwind + Vite stack from owner materials; do not rewrite that stack casually during unrelated work
- `DocumentSource` includes `news` in addition to the original guide's source types because the RAG module depends on it

## Required Artifacts

- Root: `feature_list.json`, `progress.md`, `session-handoff.md`, `init.sh`
- Shared docs: `ARCHITECTURE.md`, `docs/INTERFACES.md`, `docs/DATA_SPEC.md`, `docs/DECISIONS.md`
- Module docs: `AGENTS.md`, `ARCHITECTURE.md`, `FEATURES.md`, `SETUP.md`, `feature_list.json`

## Definition of Done

A feature is done only when all of the following are true:

- target behavior or harness update is implemented
- required verification actually ran
- evidence is recorded in the relevant `feature_list.json` or `progress.md`
- the repo remains restartable from `./init.sh`

## End of Session

1. Update `progress.md`
2. Update the relevant `feature_list.json`
3. Record blockers or risks
4. Leave the repo runnable from `./init.sh`

