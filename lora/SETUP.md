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

Real mode requires model assets:

```bash
LORA_USE_MOCK=false LORA_MODEL_PATH=/path/to/model_or_adapter python -c "from src.inference import predict_sentiment; print(predict_sentiment('Bitcoin ETF approved'))"
```

If `LORA_USE_MOCK=false` is set without `LORA_MODEL_PATH`, the wrapper raises `RuntimeError`.

## AutoDL Remote Inference

The real LoRA model is deployed outside this repository on an AutoDL server. Local code is prepared to call it later through HTTP:

```bash
LORA_USE_MOCK=false \
LORA_REMOTE_BASE_URL=https://your-autodl-host.example \
LORA_REMOTE_API_KEY=optional-token \
python -c "from src.inference import predict_sentiment; print(predict_sentiment('Bitcoin ETF approved'))"
```

Expected AutoDL endpoints:

- `POST /predict_sentiment` with `{"text": "..."}`
- `POST /batch_predict_sentiment` with `{"texts": ["...", "..."]}`
- `POST /generate_response` with `{"prompt": "...", "context": "...", "max_tokens": 512}`

Expected response shapes match `shared/types.py`: sentiment responses include `label`, `confidence`, and `scores`; generation responses include `text` and optional `model_name`.

## Verification

```bash
.venv/bin/python -m compileall src scripts
bash -n scripts/inference/start_llm.sh scripts/inference/start_llm_test.sh scripts/monitor/run_tensorboard.sh scripts/train/run_train_ift.sh scripts/train/run_train_senti.sh
.venv/bin/python -m pytest tests -q
```
