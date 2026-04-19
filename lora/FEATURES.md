# LoRA 模块功能清单

## 规则

- 一次只在一个功能上工作
- 只有当所有验证标准都通过后，该功能才算完成
- 模型训练后必须记录客观指标

## 功能列表

### LORA-001: 多源数据收集与统一格式化（priority: 1）

- **描述**：收集 IFT 数据和情绪分类数据，并清洗为统一训练格式。
- **验证标准**:
  - [ ] 成功整理 FinGPT 与 FinQA 数据
  - [ ] 成功整理 Crypto 情绪分类数据集
  - [ ] 至少抓取 10,000 条包含 Crypto 关键词的无标签社交媒体数据
  - [ ] 数据格式符合 LLaMA-Factory 要求
  - [ ] 文本清洗完成

### LORA-002: 价格弱监督打标（priority: 2）

- **描述**：基于价格时间窗口为无标签社交媒体文本生成情绪标签。
- **验证标准**:
  - [ ] 弱监督脚本运行无报错
  - [ ] 产出 Bullish / Bearish / Neutral 标签
  - [ ] 标签分布合理，未极度失衡

### LORA-003: 阶段一 LoRA-IFT 微调（priority: 3）

- **描述**：完成第一阶段金融指令微调。
- **验证标准**:
  - [ ] 训练配置正确
  - [ ] 训练脚本成功启动且 loss 下降
  - [ ] 保存 `stage1_ift` checkpoint
  - [ ] 保存评估结果

### LORA-004: 阶段二 LoRA-Sentiment 微调与评估（priority: 4）

- **描述**：完成第二阶段情绪微调与评估。
- **验证标准**:
  - [ ] 训练配置正确
  - [ ] 宏平均 F1 >= 0.80
  - [ ] Bullish / Bearish 单类 F1 >= 0.75
  - [ ] 保存评估结果
  - [ ] 成功保存最终 LoRA 权重

### LORA-005: LLM 推理管线与接口封装（priority: 5）

- **描述**：封装 `predict_sentiment()` 与 `generate_response()` 接口。
- **验证标准**:
  - [ ] `predict_sentiment()` 返回合法 `SentimentResult`
  - [ ] `generate_response()` 返回干净文本
  - [ ] LLM JSON 幻觉场景有 fallback
  - [ ] 接口签名与 `docs/INTERFACES.md` 一致

