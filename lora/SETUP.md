# LoRA Module Setup

## Prerequisites

- Python 3.10+
- GPU runtime for real training and inference
- CPU-only local environment is enough for harness and mock interface checks

## Local Harness Environment

```bash
cd lora
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The checked-in `requirements.txt` is intentionally minimal for local harness verification. GPU training dependencies such as PyTorch CUDA wheels, LLaMA-Factory, DeepSpeed, and FlashAttention should be installed in the training environment that matches the available CUDA runtime.

## Mock Interface Mode

Default local integration mode:

```bash
LORA_USE_MOCK=true .venv/bin/python -m pytest tests -q
```

Real mode uses the AutoDL vLLM service through an SSH tunnel:

```bash
LORA_USE_MOCK=false \
LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1 \
LORA_REMOTE_API_KEY=$LORA_REMOTE_API_KEY \
python -c "from src.inference import predict_sentiment; print(predict_sentiment('Bitcoin ETF approved'))"
```

If `LORA_USE_MOCK=false` is set without `LORA_REMOTE_BASE_URL`, the wrapper raises `RuntimeError`.

## AutoDL Remote Inference

The real LoRA model is deployed outside this repository on an AutoDL server. It exposes an OpenAI-compatible vLLM API through local SSH port forwarding:

```bash
ssh -CNg -L 6006:127.0.0.1:6006 -p <port> root@<AutoDL-host>
```

Local base URL:

```bash
LORA_REMOTE_BASE_URL=http://127.0.0.1:6006/v1
```

The API key must be supplied locally through `LORA_REMOTE_API_KEY`; do not commit real keys.

Expected AutoDL models:

- `sentiment-lora` for `predict_sentiment`
- `ift-lora` for `generate_response`
- `llama3.1-8b-instruct` as a base fallback

The wrapper calls `POST /chat/completions` and parses the OpenAI-compatible `choices[0].message.content` response.

## Verification

```bash
.venv/bin/python -m compileall src scripts
bash -n scripts/inference/start_llm.sh scripts/inference/start_llm_test.sh scripts/monitor/run_tensorboard.sh scripts/train/run_train_ift.sh scripts/train/run_train_senti.sh
.venv/bin/python -m pytest tests -q
```
