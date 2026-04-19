# LoRA Module AGENTS

Work only inside `lora/` unless the task explicitly requires integration changes.

## Read Order

1. `lora/ARCHITECTURE.md`
2. `lora/FEATURES.md`
3. `lora/feature_list.json`
4. `docs/INTERFACES.md` for provider contract details

## Working Rules

- Keep training and inference concerns separated
- Do not commit large datasets or checkpoints
- Any public inference signature change must be reflected in `docs/INTERFACES.md` and `shared/types.py`

## Verification

- `pip install -r requirements.txt`
- module-specific train or eval commands from `SETUP.md`

