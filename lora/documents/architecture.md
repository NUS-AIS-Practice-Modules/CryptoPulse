# LoRA 微调模块架构

## 一句话概述
对 Llama-3.1-8B-Instruct  基座模型进行两阶段 LoRA 微调 ，产出 LoRA-IFT（金融逻辑推理）和 LoRA-Sentiment（加密货币情绪分类）两个适配器，为 Chatbot 提供基于大语言模型的推断与分类引擎。

## 技术栈
- **基座模型**: Llama-3.1-8B-Instruct (零样本能力强，指令遵从度高，适合处理中英混杂的加密货币语料)。
- **微调框架**: LLaMA-Factory  (统一、高效的微调工作流，通过 YAML 驱动，降低工程踩坑率)。
- **底层加速**: PyTorch + DeepSpeed ZeRO-2/3 (显存优化)。
- **LoRA 配置**: rank=16, alpha=32, target_modules=[q_proj, k_proj, v_proj, o_proj]。
- **硬件需求**: 单卡或多卡 RTX 3090 24GB (单卡即可跑通 8B 模型的低秩微调，多卡环境可支持大规模自采推特数据的预处理及并行实验)。

## 两个微调任务

### 阶段一：LoRA-IFT (指令微调)
- **目标**: 注入通用金融知识，使模型理解金融逻辑与复杂数值推理。
- **数据来源**: FinGPT-sentiment-train  + FinQA 。
- **数据流**: 将原始问答转化为统一的 System-Instruction-Input-Output 格式，交由 LLaMA-Factory 处理。
- **数据量**: 预估整合后 5w-8w 条清洗数据。 [cite: 480]
- **训练轮数**: 2-3 Epochs。 [cite: 481]

### 阶段二：LoRA-Sentiment (加密情绪微调)
- **目标**: 在 IFT 权重基础上，注入高波动的 Crypto 市场属性，实现精准的情感分类。
- **数据来源**: CryptoBERT Dataset + TimKoornstra/financial-tweets-sentiment + Twitter 实时流自爬取数据。
- **弱监督标注**: 对 Twitter 无标签数据，基于对应时间窗口的加密资产价格变动率（如 24h $\Delta > 3\%$ 标为看涨信号）进行自动标注。
- **数据量**: 预估 2w-5w 条。 [cite: 486]
- **训练轮数**: 3-5 Epochs

## 对外接口与 LLM 接入机制



### 模型加载与接入 (LLM Integration)
- **权重管理**: 在推理阶段，可以单独加载 LoRA 权重。或与Llama-3.1 基座模型进行 **Merge (权重合并)**，IFT 权重进行 **Merge (权重合并)**，导出为一个独立的高效推理模型。
- **推理引擎**: 采用 `vLLM`  部署，以提高并发推理速度。



## 目录结构

结合 LLaMA-Factory 工作流与工程最佳实践，本模块目录结构设计如下：

```text
lora/
├── src/
│   ├── data_prep/                     # 数据流水线与预处理
│   │   ├── twitter_scraper.py         # 推特自爬取与数据清洗脚本
│   │   └── build_dataset.py           # 数据格式化 (转为 LLaMA-Factory 要求的 JSON)
│   ├── inference/                     # LLM 推理引擎接入层
│   │   ├── llm_engine.py              # 加载基座+LoRA合并权重，初始化推理后端
│   │   └── api_wrapper.py             # 封装暴露给 Chatbot 的 Python 函数
│   └── evaluation/                    # 自动化评估模块
│       └── metrics_calc.py            # 计算 Macro-F1, Accuracy 等指标
├── configs/                           # LLaMA-Factory 训练配置文件
│   ├── llama3_lora_ift.yaml           # 第一阶段：通用金融微调配置
│   └── llama3_lora_sentiment.yaml     # 第二阶段：加密情绪极性微调配置
├── scripts/                           # 自动化 Shell 脚本
│   ├── run_train_ift.sh               # 一键启动 IFT 训练
│   ├── run_train_sentiment.sh         # 一键启动 Sentiment 训练
│   └── merge_weights.sh               # 将 LoRA 权重合并入基座模型的脚本
├── data/                              # 数据集目录 (.gitignore)
│   ├── raw/                           # 原始下载的 FinGPT/FinQA/推特数据
│   └── processed/                     # 预处理后带 dataset_info.json 的标准数据集
├── checkpoints/                       # 训练产出的 Adapter 权重目录 (.gitignore)
│   ├── stage1_ift_latest/             
│   └── stage2_sentiment_latest/       
├── requirements.txt                   # 本模块专属 Python 依赖
└── README.md                          # 模块级说明文档