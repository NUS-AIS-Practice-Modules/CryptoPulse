# RAG 模块功能清单

## 规则

- 一次只做一个功能
- 验证通过才算完成
- 检索质量必须有量化指标
- 接口签名必须与 Harness 契约一致

## 功能列表

### RAG-001: 语料采集与标准化（priority: 1）

- **描述**：收集白皮书、监管文件、市场研究报告、历史案例、新闻与社媒内容，统一转换为可索引的标准文档结构。
- **验证标准**:
  - [ ] 覆盖六类来源
  - [ ] 每条文档包含 `title/content/source/url/published_at/metadata`
  - [ ] `metadata` 至少包含固定字段集
  - [ ] 原始输入转换为统一文本格式
  - [ ] 去噪与去重完成

### RAG-002: 分块、元数据建模与索引入库（priority: 2）

- **描述**：执行分块、embedding 和索引入库。
- **验证标准**:
  - [ ] 分块逻辑可运行
  - [ ] `BAAI/bge-m3` 可正常加载
  - [ ] Milvus collection 创建成功
  - [ ] BM25 索引构建成功
  - [ ] `index_documents()` 返回正确索引数

### RAG-003: Dense Retrieval 实现（priority: 3）

- **描述**：实现基于向量索引的语义检索。
- **验证标准**:
  - [ ] 基础检索问题返回相关结果
  - [ ] `FTX collapse` 类查询 Top-5 命中案例复盘或新闻
  - [ ] raw dense retrieval 延迟 `< 1.5s`
  - [ ] 返回字段齐全

### RAG-004: BM25 检索与混合融合（priority: 4）

- **描述**：实现 BM25 和 RRF 融合。
- **验证标准**:
  - [ ] BM25 可独立运行
  - [ ] `Recall@5 >= 0.75`
  - [ ] `source_filter` 对六类来源生效

### RAG-005: Rerank 与 Chatbot 接口封装（priority: 5）

- **描述**：加入 reranker 并封装对外接口。
- **验证标准**:
  - [ ] `retrieve()` 签名与契约一致
  - [ ] `get_context_for_llm()` 签名与契约一致
  - [ ] 返回可直接拼入 prompt 的上下文
  - [ ] `get_context_for_llm()` 延迟 `< 3s`

### RAG-006: 定时刷新与评估优化（priority: 6）

- **描述**：实现新闻与社媒定时刷新，并跑 benchmark / RAGAS 评估。
- **验证标准**:
  - [ ] 定时刷新 job 可运行
  - [ ] 输出 Recall@K、延迟、Faithfulness 等指标
  - [ ] `Generation Faithfulness >= 85%`
  - [ ] 刷新失败不破坏既有索引

