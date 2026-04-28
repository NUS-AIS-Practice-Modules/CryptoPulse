# LoRA Module AGENTS.md

This module owns LoRA training, sentiment inference, and response-generation wrappers for Chatbot.

## Startup Workflow

1. Work from `lora/`
2. Read `ARCHITECTURE.md`
3. Read `FEATURES.md`
4. Read `SETUP.md`
5. Check `feature_list.json`
6. Work on one feature at a time
7. Record verification evidence before marking a feature passing

## Boundaries

LoRA owns:

- Data preparation scripts for instruction and sentiment fine-tuning
- Training configuration for LLaMA-Factory
- The Chatbot-facing Python functions:
  - `predict_sentiment(text: str)`
  - `batch_predict_sentiment(texts: list[str])`
  - `generate_response(prompt: str, context: str = "", max_tokens: int = 512)`

LoRA does not own:

- Frontend UI
- Chatbot REST routing
- RAG indexing or retrieval

## Mock Strategy

The inference wrapper defaults to a deterministic mock/fallback mode so Chatbot can integrate before GPU training is complete. The real LoRA runtime is expected on an AutoDL OpenAI-compatible vLLM server; set `LORA_USE_MOCK=false` with `LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1` after opening the SSH tunnel.

## Verification

Minimum local checks:

```bash
python -m compileall src scripts
bash -n scripts/inference/start_llm.sh scripts/inference/start_llm_test.sh scripts/monitor/run_tensorboard.sh scripts/train/run_train_ift.sh scripts/train/run_train_senti.sh
python -m pytest tests -q
```
