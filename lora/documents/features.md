# LoRA 模块功能清单

## 规则
- 一次只在一个功能（Feature）上工作。
- 只有当所有的“验证标准”都通过后，该功能才算完成（Passing）。
- 模型训练完成后，必须运行评估脚本并记录客观指标（Metrics）。

## 功能列表

### LORA-001: 多源数据收集与统一格式化 (Priority: 1)
- **描述**: 
  - **IFT数据集处理**: 收集 FinGPT、FinQA 数据集，将其清洗并统一转化为 LLaMA-Factory 支持的 JSON 格式（包含 `instruction`, `input`, `output` 字段），用于后续的指令微调阶段。
  - **情绪分类数据集处理**: 收集 CryptoBERT 数据集、从 https://github.com/abTuring13/CryptoBERT 项目下载的情绪分析数据集、TimKoornstra/financial-tweets-sentiment 数据集（包含两种数据类型），并补充自爬取的多源社交媒体数据。将所有情绪相关数据清洗并统一格式，用于后续的情绪分类微调。
    - **爬虫功能技术细节 (2026/04 更新)**: 
      - **Twitter/X 数据收集**: 使用 snscrape 库（无需API密钥）或 Twitter API v2（每月限额1500条）抓取包含加密货币关键词（如 #BTC, #ETH, #Crypto）的实时推文。支持时间范围过滤和地理位置过滤。
      - **Reddit 数据收集**: 使用 PRAW 库连接 Reddit API，抓取 r/cryptocurrency, r/bitcoin 等子版块的评论和帖子。支持关键词搜索和时间窗口设置。
      - **Telegram 数据收集**: 使用 Telethon 库连接 Telegram API，抓取加密货币相关群组（如币安、火币等）的消息。需要用户账户授权，支持历史消息回溯。
      - **StockTwits 数据收集**: 使用官方API或网页抓取工具收集股票和加密货币讨论数据。支持实时流和历史数据查询。
      - **数据预处理**: 自动去除重复帖子、短文本（<4词）、URL、@提及、特殊字符。统一时间戳格式，支持多语言检测和过滤。
- **验证标准**:
  - [ ] 成功下载并合并 FinGPT-sentiment-train、FinQA 数据作为IFT数据集。
  - [ ] 成功下载并合并 ElKulako/stocktwits-crypto、abTuring13/CryptoBERT 情绪分析数据集以及 TimKoornstra/financial-tweets-sentiment 数据集作为情绪分类数据集。
  - [ ] 多源爬虫脚本可运行，从 Twitter、Reddit、Telegram、StockTwits 至少四种来源成功抓取总计至少 10,000 条包含 Crypto 关键词的无标签社交媒体数据。
  - [ ] 所有数据集格式完全符合 LLaMA-Factory 的要求，无空值、无乱码，并正确注册到 `dataset_info.json` 中。
  - [ ] 文本清洗完成（去除 URL、多余的 @mention、特殊不可见字符）。

### LORA-002: Twitter 数据的价格弱监督打标 (Priority: 2)
- **描述**: 针对自爬取的无标签 Twitter 数据，利用对应时间窗口的加密货币价格变动率（如 24h $\Delta$）作为信号，进行弱监督情感标注（Bullish/Bearish/Neutral）。
  - **价格信息来源与获取**:
    - **数据源**: 使用 CoinGecko API（免费，无需API密钥）或 Binance API 获取实时和历史加密货币价格数据。CoinGecko 提供超过 10,000 种加密货币的价格信息，支持多时间框架的历史数据查询。
    - **API 调用方式**: 使用 `pycoingecko` Python 库或直接 HTTP 请求获取 OHLCV 数据（开盘价、最高价、最低价、收盘价、成交量）。支持按币种（如 BTC, ETH）和时间间隔（1h, 24h）查询。
    - **数据存储**: 将获取的价格数据存储为 CSV 或 SQLite 数据库，包含时间戳、币种、价格、24h变动率等字段。定期更新以覆盖推文时间范围。
  - **技术细节设计**:
    - **时间窗口匹配**: 对于每条推文，根据其时间戳，计算 24 小时价格变动率 $\Delta = \frac{P_{current} - P_{24h\_ago}}{P_{24h\_ago}} \times 100\%$。如果推文时间无精确匹配，使用线性插值或最近邻价格。
    - **币种识别**: 使用正则表达式或 NLP 工具（如 spaCy）识别推文中提到的币种（如 #BTC, Bitcoin, $ETH）。支持主流币种映射表，未识别币种默认为 BTC。
    - **标注阈值**: 
      - Bullish: $\Delta \geq +5\%$
      - Bearish: $\Delta \leq -5\%$
      - Neutral: $-5\% < \Delta < +5\%$
      - 可配置阈值以调整敏感度。
    - **数据质量控制**: 过滤异常价格波动（如闪崩事件），使用移动平均线平滑数据。确保标注分布均衡，避免过度偏向 Neutral。
    - **批量处理**: 脚本支持并行处理大量推文，使用多线程获取价格数据，处理速率至少 1000 条/分钟。
- **验证标准**:
  - [ ] 弱监督标注逻辑脚本（`data_prep.py`）运行无报错。
  - [ ] 标注结果正确映射为 Bullish、Bearish、Neutral 三类，且分布相对合理（防止 90% 以上全是 Neutral）。

  - [ ] 最终产出用于第二阶段微调的 Crypto Sentiment 混合数据集。

### LORA-003: 阶段一 LoRA-IFT 通用金融指令微调 (Priority: 3)
- **描述**: 使用 LLaMA-Factory 在 FinGPT+FinQA 混合数据集上对 Llama-3-8B-Instruct 进行第一阶段微调，注入基础金融推理能力。
- **验证标准**:
  - [ ] `configs/llama3_lora_ift.yaml` 配置正确（模型路径、数据集名称、LoRA 参数无误）。
  - [ ] 训练脚本 `run_train_ift.sh` 成功在 GPU 上启动，显存分配合理（无 OOM），Loss 曲线呈现稳定下降趋势。保存Loss曲线
  - [ ] 训练完成后，成功保存 stage1_ift 的 Checkpoint。同时进行evaluation，保存评估结构。
  - [ ] 抽取 10 个 FinQA 测试样本进行人工检查，模型能正确遵从指令并给出金融逻辑分析。

### LORA-004: 阶段二 LoRA-Sentiment 加密情绪微调与评估 (Priority: 4)
- **描述**: 基于阶段一的 Checkpoint，在 CryptoBERT + 弱监督 Twitter 数据集上进行第二阶段情感分类微调。
- **验证标准**:
  - [ ] `configs/llama3_lora_sentiment.yaml` 配置正确（注意加载 stage1 的 adapter 权重或基于 merge 后的权重训练）。
  - [ ] 训练顺利完成，在保留的测试集上运行自动化评估脚本。
  - [ ] 宏平均 F1 分数 (Macro-F1) $\ge 0.80$。
  - [ ] 极性类别（Bullish / Bearish）的单类 F1-Score 分别 $\ge 0.75$。
  - [ ] 保存evaluation结果
  - [ ] 成功执行合并脚本，独立保存最终的 LoRA 权重。

### LORA-005: LLM 推理管线与 API 接口封装 (Priority: 5)
- **描述**: 基于合并后的 Llama-3 模型，封装供 Chatbot 调用的 `predict_sentiment()` 和 `generate_response()` Python 接口，并确保 JSON 解析的鲁棒性。
- **验证标准**:
  - [ ] `predict_sentiment("Bitcoin ETF is getting approved tomorrow, to the moon!")` 能够稳定返回包含 `label` (Bullish) 和 `confidence` 的 `SentimentResult` 数据类。
  - [ ] `generate_response(prompt, context)` 能够正确截断 Llama-3 的 `<|eot_id|>` 特殊字符，返回干净的文本字符串。
  - [ ] 针对 LLM 偶尔不输出标准 JSON 的幻觉情况，具备正则表达式 fallback 提取机制。
