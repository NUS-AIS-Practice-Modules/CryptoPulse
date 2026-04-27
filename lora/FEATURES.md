# LoRA Module Features

## LORA-001: Multi-source Dataset Preparation

Prepare instruction-tuning and sentiment datasets in LLaMA-Factory format.

Verification:

- Dataset scripts run without syntax errors
- Output records include `instruction`, `input`, and `output`
- Dataset registration is documented

## LORA-002: Weak-supervision Labeling

Use crypto price movement windows to label unlabeled social posts as Bullish, Bearish, or Neutral.

Verification:

- Labeling logic maps records to the three shared sentiment labels
- Output distribution is documented and not overwhelmingly single-class

## LORA-003: Stage 1 LoRA-IFT Training

Fine-tune the base model on general financial instruction data.

Verification:

- Training config is valid
- Training job starts on a suitable GPU runtime
- Loss and checkpoint evidence are recorded

## LORA-004: Stage 2 LoRA-Sentiment Training

Fine-tune sentiment behavior using crypto sentiment data.

Verification:

- Training config is valid
- Evaluation reports Macro-F1 and per-class F1
- Final adapter or merged model location is documented

## LORA-005: Chatbot-facing Inference Wrapper

Expose `predict_sentiment`, `batch_predict_sentiment`, and `generate_response`.

Verification:

- Functions return `shared/types.py` dataclasses in mock/fallback mode
- Empty inputs raise `ValueError`
- Real mode without model configuration raises a clear `RuntimeError`
