# CryptoPulse System Architecture

## Summary

CryptoPulse is organized as four collaborating modules:

- `frontend`: browser client and dashboard UX
- `chatbot`: API and orchestration layer
- `lora`: fine-tuned model training and inference
- `rag`: knowledge ingestion, retrieval, and context assembly

The system is intentionally split so that `lora` and `rag` can be developed in parallel, `chatbot` integrates both, and `frontend` consumes the public API exposed by `chatbot`.

## System Topology

```text
User (Browser)
   |
   | HTTP / optional streaming later
   v
Frontend Module
   |
   | REST API
   v
Chatbot Module
   | \
   |  \
   |   \ Python function calls
   v    v
LoRA   RAG
```

## Module Responsibilities

| Module | Core responsibility | Primary outputs |
|--------|---------------------|-----------------|
| Frontend | Chat UI, dashboard UI, upload UI, user interaction | Web app that calls Chatbot APIs |
| Chatbot | Integration pipeline, REST API, conversation handling, NER | `/api/chat`, `/api/sentiment/summary`, `/api/health` |
| LoRA | Two-stage LoRA training, sentiment inference, response generation | Fine-tuned checkpoints and Python inference functions |
| RAG | Knowledge ingestion, indexing, hybrid retrieval, context formatting | Python retrieval functions for Chatbot |

## Dependency Order

```text
Frontend -> Chatbot
Chatbot -> LoRA
Chatbot -> RAG
LoRA -> independent during training
RAG -> independent during indexing
```

Implications:

- `lora` and `rag` can move in parallel
- `chatbot` should support `USE_MOCK=true` while providers are not ready
- `frontend` should also support mock or partially available backend behavior while APIs stabilize

## Integration Contracts

- Frontend consumes Chatbot via REST
- Chatbot consumes LoRA and RAG via Python functions
- Shared backend types live in `shared/types.py`
- Source-of-truth interface definitions live in `docs/INTERFACES.md`

## Delivery Timeline

- Weeks 1-2: dataset prep across LoRA, RAG, and Chatbot
- Weeks 3-5: LoRA training and NER work
- Weeks 4-6: RAG implementation and retrieval evaluation
- Weeks 6-7: Chatbot integration and Frontend end-to-end testing
- Weeks 7-8: evaluation, demo preparation, report completion
- Course deadline: `2026-05-10`

## Development Model

- mock-first until providers are integration-ready
- one feature at a time inside a single module unless explicitly doing integration
- interface changes are coordination events
- verification evidence is required before claiming a milestone is complete

