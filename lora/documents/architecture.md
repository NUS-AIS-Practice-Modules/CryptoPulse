# LoRA Fine-Tuning Module Architecture

## One-Line Summary

This module applies two-stage LoRA fine-tuning to the Llama-3.1-8B-Instruct base model and produces two adapters, LoRA-IFT (financial reasoning) and LoRA-Sentiment (cryptocurrency sentiment classification), to provide Chatbot with an LLM-based reasoning and classification engine.

## Tech Stack

- **Base model**: Llama-3.1-8B-Instruct (strong zero-shot ability, good instruction following, suitable for mixed English/Chinese crypto corpora)
- **Fine-tuning framework**: LLaMA-Factory (a unified and efficient YAML-driven fine-tuning workflow that reduces engineering friction)
- **Acceleration layer**: PyTorch + DeepSpeed ZeRO-2/3 (VRAM optimization)
- **LoRA config**: `rank=16`, `alpha=32`, `target_modules=[q_proj, k_proj, v_proj, o_proj]`
- **Hardware requirement**: single or multi-GPU RTX 3090 24GB setup (one card is enough to run low-rank fine-tuning on an 8B model; multi-GPU environments can support larger self-collected Twitter preprocessing and parallel experiments)

## Two Fine-Tuning Tasks

### Stage 1: LoRA-IFT (Instruction Fine-Tuning)

- **Goal**: Inject general financial knowledge so the model can understand financial logic and complex numerical reasoning.
- **Data sources**: FinGPT-sentiment-train + FinQA
- **Data flow**: Convert raw QA data into a unified `System-Instruction-Input-Output` format and feed it to LLaMA-Factory.
- **Data volume**: Estimated 50k-80k cleaned samples. [cite: 480]
- **Training epochs**: 2-3 epochs. [cite: 481]

### Stage 2: LoRA-Sentiment (Crypto Sentiment Fine-Tuning)

- **Goal**: Build on top of the IFT weights and inject high-volatility crypto market characteristics for precise sentiment classification.
- **Data sources**: CryptoBERT Dataset + TimKoornstra/financial-tweets-sentiment + self-collected real-time Twitter data
- **Weak supervision**: For unlabeled Twitter data, automatically label samples using the price-change rate of the related crypto asset over a matching time window, for example labeling `24h Δ > 3%` as a bullish signal.
- **Data volume**: Estimated 20k-50k samples. [cite: 486]
- **Training epochs**: 3-5 epochs

## Public Interface and LLM Integration

### Model Loading and Integration

- **Weight management**: At inference time, LoRA weights can be loaded independently, or merged into the Llama-3.1 base model. The IFT weights can be merged and exported as an efficient standalone inference model.
- **Inference engine**: Deploy with `vLLM` to improve concurrent inference throughput.

## Directory Layout

Aligned with the LLaMA-Factory workflow and common engineering practices, the module layout is:

```text
lora/
├── src/
│   ├── data_prep/                     # Data pipelines and preprocessing
│   │   ├── twitter_scraper.py         # Twitter scraping and data-cleaning script
│   │   └── build_dataset.py           # Data formatting into LLaMA-Factory JSON
│   ├── inference/                     # LLM inference integration layer
│   │   ├── llm_engine.py              # Load merged base+LoRA weights and initialize the inference backend
│   │   └── api_wrapper.py             # Python functions exposed to Chatbot
│   └── evaluation/                    # Automated evaluation module
│       └── metrics_calc.py            # Computes Macro-F1, Accuracy, and similar metrics
├── configs/                           # LLaMA-Factory training configs
│   ├── llama3_lora_ift.yaml           # Stage 1: general financial tuning config
│   └── llama3_lora_sentiment.yaml     # Stage 2: crypto sentiment tuning config
├── scripts/                           # Automation shell scripts
│   ├── run_train_ift.sh               # One-command IFT training
│   ├── run_train_sentiment.sh         # One-command sentiment training
│   └── merge_weights.sh               # Merge LoRA weights into the base model
├── data/                              # Dataset directory (.gitignore)
│   ├── raw/                           # Raw FinGPT / FinQA / Twitter data
│   └── processed/                     # Preprocessed standardized datasets with dataset_info.json
├── checkpoints/                       # Adapter checkpoints produced by training (.gitignore)
│   ├── stage1_ift_latest/
│   └── stage2_sentiment_latest/
├── requirements.txt                   # Module-specific Python dependencies
└── README.md                          # Module-level documentation
```
