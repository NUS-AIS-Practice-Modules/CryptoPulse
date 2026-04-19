# Chatbot Module Feature List

## Rules

- Work on one feature at a time
- A feature is only complete when all verification criteria pass
- Every API endpoint must have a corresponding test
- Mock verification must pass before integration tasks

## Feature List

### CB-001: API Service Skeleton (priority: 1)

- **Description**: Initialize the FastAPI project, register routes, implement the health check endpoint, and verify the service starts correctly.
- **Verification Criteria**:
  - [ ] `pip install -r requirements.txt` completes without errors
  - [ ] `uvicorn src.app:app --reload` starts without errors
  - [ ] `GET /api/health` returns HTTP 200 with `status: "ok"`
  - [ ] `http://localhost:8000/docs` is available

### CB-001b: LLM-based NER Implementation (priority: 2)

- **Description**: Implement `llm_ner.py` and `ner_service.py`.
- **Verification Criteria**:
  - [ ] Entity extraction returns expected crypto entities for a sample sentence
  - [ ] Output matches `Entity` shape in `shared/types.py`
  - [ ] Offset correction is done via string matching
  - [ ] Invalid JSON from the LLM is handled gracefully
  - [ ] `NER_BACKEND=llm` routes correctly

### CB-004: Conversation Generation Pipeline (priority: 3)

- **Description**: Implement NER -> sentiment -> retrieval -> generation with mocks first.
- **Verification Criteria**:
  - [ ] `POST /api/chat` returns HTTP 200 with `USE_MOCK=true`
  - [ ] Response contains `reply`, `sentiment`, `entities`, `sources`, and `conversation_id`
  - [ ] In-memory conversation history works across turns
  - [ ] Different `conversation_id` values remain isolated
  - [ ] Mock-mode latency < 3 seconds

### CB-005: Sentiment Trend Summary (priority: 4)

- **Description**: Implement `GET /api/sentiment/summary`.
- **Verification Criteria**:
  - [ ] Supported periods return HTTP 200
  - [ ] Response contains trend data and top topics
  - [ ] Unsupported periods return HTTP 422
  - [ ] Mock data latency < 1 second

### CB-006: Integration with Real LoRA + RAG (priority: 5)

- **Description**: Replace mocks with real provider module calls.
- **Verification Criteria**:
  - [ ] Service starts normally with `USE_MOCK=false`
  - [ ] `predict_sentiment()` succeeds
  - [ ] `get_context_for_llm()` returns non-empty context
  - [ ] LLM API call returns non-empty reply
  - [ ] `/api/health` reports `lora` and `rag` as ok
  - [ ] `pytest tests/` passes

