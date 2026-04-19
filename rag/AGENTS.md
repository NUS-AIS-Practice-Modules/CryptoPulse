# RAG Module AGENTS

Work inside `rag/` unless the task is explicitly about integration or shared contracts.

## Read Order

1. `rag/ARCHITECTURE.md`
2. `rag/FEATURES.md`
3. `rag/feature_list.json`
4. `docs/INTERFACES.md`

## Working Rules

- Preserve the documented hybrid retrieval design unless an explicit decision changes it
- Do not commit local vector store contents or raw corpora
- Keep retrieval contract compatibility with Chatbot

## Verification

- `pip install -r requirements.txt`
- retrieval, indexing, and evaluation commands from `SETUP.md`

