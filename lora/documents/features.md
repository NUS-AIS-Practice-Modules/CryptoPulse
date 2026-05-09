# LoRA Module Feature List

## Rules

- Work on only one feature at a time.
- A feature counts as complete only after all verification criteria pass.
- After model training finishes, an evaluation script must run and objective metrics must be recorded.

## Features

### LORA-001: Multi-Source Data Collection and Unified Formatting (Priority: 1)

- **Description**:
  - **IFT dataset processing**: Collect FinGPT and FinQA datasets, clean them, and convert them into the JSON format required by LLaMA-Factory (including `instruction`, `input`, and `output` fields) for the later instruction-tuning stage.
  - **Sentiment-classification dataset processing**: Collect the CryptoBERT dataset, the sentiment dataset from the `abTuring13/CryptoBERT` project, the `TimKoornstra/financial-tweets-sentiment` dataset (with two data types), and additional self-collected multi-source social-media data. Clean and normalize all sentiment-related data into one format for later sentiment fine-tuning.
    - **Crawler technical details (2026/04 update)**:
      - **Twitter/X data collection**: Use the `snscrape` library (no API key required) or Twitter API v2 (monthly cap of 1500 items) to collect real-time tweets containing cryptocurrency keywords such as `#BTC`, `#ETH`, and `#Crypto`. Supports time-range and geo filters.
      - **Reddit data collection**: Use the `PRAW` library with the Reddit API to collect posts and comments from subreddits such as `r/cryptocurrency` and `r/bitcoin`. Supports keyword search and time-window filters.
      - **Telegram data collection**: Use the `Telethon` library with the Telegram API to collect messages from crypto-related groups. Requires user account authorization and supports historical message backfill.
      - **StockTwits data collection**: Use the official API or web-scraping tools to collect stock and crypto discussion data. Supports real-time streams and historical lookups.
      - **Data preprocessing**: Automatically remove duplicate posts, short texts (`< 4` words), URLs, `@mentions`, and special characters. Normalize timestamps and support language detection and filtering.
- **Verification**:
  - [ ] FinGPT-sentiment-train and FinQA are successfully downloaded, merged, and prepared as the IFT dataset.
  - [ ] ElKulako/stocktwits-crypto, abTuring13/CryptoBERT, and TimKoornstra/financial-tweets-sentiment are successfully downloaded, merged, and prepared as the sentiment dataset.
  - [ ] Multi-source crawler scripts run successfully and collect at least 10,000 unlabeled crypto-keyword social-media samples across at least four sources: Twitter, Reddit, Telegram, and StockTwits.
  - [ ] All dataset formats fully satisfy LLaMA-Factory requirements, contain no empty values or mojibake, and are correctly registered in `dataset_info.json`.
  - [ ] Text cleaning is complete, including removal of URLs, redundant `@mentions`, and invisible special characters.

### LORA-002: Price-Based Weak Supervision for Twitter Data (Priority: 2)

- **Description**: For self-collected unlabeled Twitter data, use the price-change rate in the corresponding time window, such as 24h `Δ`, as a signal to generate weakly supervised sentiment labels (`Bullish` / `Bearish` / `Neutral`).
  - **Price data source and retrieval**:
    - **Data source**: Use the CoinGecko API (free, no API key required) or Binance API to fetch real-time and historical cryptocurrency prices. CoinGecko covers more than 10,000 crypto assets and supports historical queries across multiple time frames.
    - **API access pattern**: Use the `pycoingecko` Python library or direct HTTP requests to fetch OHLCV data (open, high, low, close, volume). Supports queries by asset symbol and time interval such as `1h` and `24h`.
    - **Data storage**: Store price data in CSV or SQLite, including timestamp, asset symbol, price, 24h change rate, and related fields. Refresh regularly to cover tweet time ranges.
  - **Technical design details**:
    - **Time-window matching**: For each tweet, compute the 24-hour price change rate using its timestamp: `Δ = (P_current - P_24h_ago) / P_24h_ago * 100%`. If an exact price timestamp is unavailable, use linear interpolation or nearest-neighbor pricing.
    - **Asset detection**: Use regex or NLP tools such as `spaCy` to detect mentioned assets, for example `#BTC`, `Bitcoin`, or `$ETH`. Support a mapping table for major assets; default to BTC when no asset is detected.
    - **Labeling thresholds**:
      - Bullish: `Δ >= +5%`
      - Bearish: `Δ <= -5%`
      - Neutral: `-5% < Δ < +5%`
      - Thresholds should remain configurable.
    - **Data-quality control**: Filter abnormal price shocks, such as crash anomalies, and smooth prices with moving averages. Keep label distribution reasonably balanced to avoid an overwhelming Neutral class.
    - **Batch processing**: The script should support parallel processing for large tweet sets, use multithreading for price fetches, and target at least 1000 items per minute.
- **Verification**:
  - [ ] The weak-supervision script (`data_prep.py`) runs without errors.
  - [ ] Output labels are correctly mapped into `Bullish`, `Bearish`, and `Neutral`, with a reasonable distribution that does not collapse into more than 90% `Neutral`.
  - [ ] The final mixed crypto-sentiment dataset for second-stage fine-tuning is produced.

### LORA-003: Stage 1 LoRA-IFT General Financial Instruction Tuning (Priority: 3)

- **Description**: Use LLaMA-Factory to fine-tune Llama-3-8B-Instruct on the mixed FinGPT+FinQA dataset as the first stage, injecting basic financial reasoning ability.
- **Verification**:
  - [ ] `configs/llama3_lora_ift.yaml` is configured correctly, including model path, dataset name, and LoRA parameters.
  - [ ] Training script `run_train_ift.sh` starts successfully on GPU, uses VRAM reasonably without OOM, and the loss curve shows a stable downward trend. Save the loss curve.
  - [ ] After training completes, the `stage1_ift` checkpoint is saved successfully. Run evaluation and save the evaluation artifacts.
  - [ ] Manually inspect 10 FinQA test samples and confirm the model follows instructions correctly and produces financial reasoning.

### LORA-004: Stage 2 LoRA-Sentiment Crypto Fine-Tuning and Evaluation (Priority: 4)

- **Description**: Starting from the stage-1 checkpoint, fine-tune sentiment classification on the CryptoBERT + weakly supervised Twitter dataset.
- **Verification**:
  - [ ] `configs/llama3_lora_sentiment.yaml` is configured correctly, especially loading the stage-1 adapter or training from merged weights.
  - [ ] Training completes successfully and the automated evaluation script runs on the held-out test set.
  - [ ] Macro-F1 score is `>= 0.80`.
  - [ ] Per-class F1 for `Bullish` and `Bearish` is each `>= 0.75`.
  - [ ] Save evaluation results.
  - [ ] Successfully run the merge script and save the final LoRA weights independently.

### LORA-005: LLM Inference Pipeline and API Wrapper (Priority: 5)

- **Description**: Based on the merged Llama-3 model, package `predict_sentiment()` and `generate_response()` Python interfaces for Chatbot and make JSON parsing robust.
- **Verification**:
  - [ ] `predict_sentiment("Bitcoin ETF is getting approved tomorrow, to the moon!")` reliably returns a `SentimentResult` dataclass containing `label` (`Bullish`) and `confidence`.
  - [ ] `generate_response(prompt, context)` correctly strips the Llama-3 `<|eot_id|>` special token and returns clean text.
  - [ ] When the LLM occasionally fails to output standard JSON, a regex-based fallback extraction path is available.
