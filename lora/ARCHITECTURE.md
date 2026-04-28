# LoRA Module Architecture

## Overview

The LoRA module fine-tunes a Llama-3.1-8B-Instruct base model in two stages and exposes lightweight Python wrappers for Chatbot integration.

## Responsibilities

- Build instruction-tuning datasets from financial QA and sentiment data
- Build crypto sentiment datasets from labeled and weakly labeled social data
- Run LLaMA-Factory LoRA training jobs
- Save and document checkpoints and evaluation outputs
- Expose Chatbot-facing inference wrappers that match `docs/INTERFACES.md`

## Tech Stack

| Component | Choice |
|-----------|--------|
| Base model | Llama-3.1-8B-Instruct |
| Fine-tuning framework | LLaMA-Factory |
| Training runtime | PyTorch + optional DeepSpeed/FlashAttention |
| Local harness runtime | Python 3.10+ |
| Integration types | `shared/types.py` dataclasses |

## Data And Training Flow

```text
Raw datasets
  -> cleaning and formatting
  -> LLaMA-Factory dataset JSON
  -> stage 1 LoRA-IFT training
  -> stage 2 LoRA-Sentiment training
  -> evaluation
  -> exported adapter or merged model
  -> Chatbot-facing inference wrappers
```

## Interface Boundary

Chatbot imports LoRA as Python functions. The wrapper currently supports deterministic mock/fallback behavior for integration testing.

The real LoRA model is deployed on an AutoDL server outside this repository. The local wrapper connects through an SSH tunnel to an OpenAI-compatible vLLM API at `LORA_REMOTE_BASE_URL`, then calls `/chat/completions` with `sentiment-lora` for sentiment classification and `ift-lora` for response generation.

## Current Implementation Notes

The historical owner documents remain in `documents/`. This root-level harness file is the canonical module summary for repository integration.
