# Chatbot Module AGENTS

Work in `chatbot/` unless the task explicitly spans provider integration or shared contracts.

## Read Order

1. `chatbot/ARCHITECTURE.md`
2. `chatbot/FEATURES.md`
3. `chatbot/feature_list.json`
4. `docs/INTERFACES.md`

## Working Rules

- Keep the REST contract stable for Frontend consumers
- Keep LoRA and RAG calls behind clear service boundaries
- Use `USE_MOCK=true` until providers are ready
- Route NER backend changes through the documented `NER_BACKEND` switch

## Verification

- `pip install -r requirements.txt`
- `uvicorn src.app:app --reload --host 0.0.0.0 --port 8000`
- endpoint checks from `SETUP.md`

