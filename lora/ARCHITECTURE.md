# LoRA 微调模块架构

## 一句话概述

对 `Llama-3-8B-Instruct` 基座模型进行两阶段 LoRA 微调，产出 `LoRA-IFT`（金融逻辑推理）和 `LoRA-Sentiment`（加密货币情绪分类）两个适配器，为 Chatbot 提供基于大语言模型的推断与分类引擎。

## 技术栈

- **基座模型**: `Llama-3-8B-Instruct`
- **微调框架**: `LLaMA-Factory`
- **底层加速**: `PyTorch + DeepSpeed ZeRO-2/3`
- **LoRA 配置**: `rank=16`, `alpha=32`, `target_modules=[q_proj, k_proj, v_proj, o_proj]`
- **硬件需求**: 单卡或多卡 RTX 3090 / 4090 24GB

## 两个微调任务

### 阶段一：LoRA-IFT

- 目标：注入通用金融知识和复杂数值推理能力
- 数据来源：`FinGPT-sentiment-train` + `FinQA`
- 数据流：统一转为 `System-Instruction-Input-Output` 格式供 `LLaMA-Factory` 使用
- 预估数据量：5w-8w 条
- 训练轮数：2-3 epochs

### 阶段二：LoRA-Sentiment

- 目标：在 IFT 权重基础上学习加密市场情绪分类
- 数据来源：`CryptoBERT Dataset`、`TimKoornstra/financial-tweets-sentiment`、自爬 Twitter 数据
- 弱监督标注：根据价格窗口涨跌进行自动标签构造
- 预估数据量：2w-5w 条
- 训练轮数：3-5 epochs

## 模型加载与接入

- 推理阶段可单独加载 LoRA 权重
- 也可与基座模型执行 merge，导出高效推理模型
- 推理引擎规划为 `vLLM`

## 对外接口

LoRA 模块向 Chatbot 暴露以下函数，详见 `docs/INTERFACES.md`：

```python
def predict_sentiment(text: str) -> SentimentResult:
    ...


def generate_response(prompt: str, context: str = "", max_tokens: int = 512) -> GenerationResult:
    ...


def batch_predict_sentiment(texts: list[str]) -> list[SentimentResult]:
    ...
```

## 目录结构

```text
lora/
├── src/
│   ├── data_prep/
│   │   ├── twitter_scraper.py
│   │   └── build_dataset.py
│   ├── inference/
│   │   ├── llm_engine.py
│   │   └── api_wrapper.py
│   └── evaluation/
│       └── metrics_calc.py
├── configs/
│   ├── llama3_lora_ift.yaml
│   └── llama3_lora_sentiment.yaml
├── scripts/
│   ├── run_train_ift.sh
│   ├── run_train_sentiment.sh
│   └── merge_weights.sh
├── data/
│   ├── raw/
│   └── processed/
├── checkpoints/
│   ├── stage1_ift_latest/
│   └── stage2_sentiment_latest/
├── requirements.txt
└── README.md
```

