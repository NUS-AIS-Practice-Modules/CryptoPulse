# RAG 模块架构

## 一句话概述

基于 `Milvus + BAAI/bge-m3 + BM25 + reranker` 构建加密货币领域 RAG 模块，覆盖白皮书、监管文件、研究报告、历史案例、实时新闻与社媒内容，为 Chatbot 提供可控、可解释的上下文增强能力。

## 技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| 向量数据库 | Milvus | 支持大规模向量索引、过滤与持久化 |
| 嵌入模型 | `BAAI/bge-m3` | 适配新闻、报告、问答与多类型文本 |
| 分块策略 | 语义优先 + 固定窗口兜底 | 平衡上下文完整性和检索效率 |
| 稀疏检索 | BM25 权重 + Milvus sparse vector | 覆盖精确匹配场景，并让 dense / sparse 检索在同一 Milvus collection 内完成 |
| 融合策略 | Milvus `hybrid_search` + `WeightedRanker` | 与 Milvus v2.6 官方方案一致，减少应用层双检索与融合开销 |
| 重排序 | 轻量 cross-encoder reranker | 优化 top-k 相关性 |

## 知识来源

- `whitepaper`
- `regulatory`
- `market_data`
- `case_study`
- `social_media`
- `news`

## 检索管线

```text
user query
   ↓
query normalize
   ↓
dense embedding + BM25 sparse vector
   ↓
Milvus hybrid_search(AnnSearchRequest + WeightedRanker)
   ↓
cross-encoder reranker
   ↓
top-k documents
   ↓
context assembly
   ↓
get_context_for_llm()
```

原始实现路径 `dense Milvus search + 外部 BM25 JSON index + RRF` 仍保留为兼容和调试路径。生产默认选择 Milvus 原生 hybrid 路径，因为它与官方 v2.6 教程一致，在单个 collection 中保存 `embedding` 与 `sparse_vector`，分别使用 `AUTOINDEX` 与 `SPARSE_INVERTED_INDEX`，查询时用 `AnnSearchRequest` 和 `WeightedRanker` 一次完成融合。

## 混合检索方案决策

对比结果：

| 方案 | 优点 | 代价 | 当前定位 |
|------|------|------|----------|
| 原始方案：Milvus dense + 应用层 BM25 + RRF | 实现直观；BM25 JSON 文件可离线检查；便于单测和降级 | 每次查询要访问两个检索后端并在应用层融合；BM25 文件和 Milvus collection 需要额外保持一致；调权只能作用在 RRF 排名层 | 保留为兼容、调试、fallback |
| 官方方案：Milvus dense+sparse native hybrid | 与 Milvus v2.6 官方教程一致；dense/sparse 字段共存于同一 collection；索引、过滤、融合都由 Milvus 处理；`WeightedRanker` 可直接调 sparse/dense 权重 | 需要在入库时生成 sparse vector；collection schema 与 dense-only collection 不兼容，需要重新建 hybrid collection | 作为默认推荐方案 |

选择：默认采用官方 Milvus 原生 hybrid 方案，原因是本模块已经依赖本地 Milvus standalone，且当前全量语料只有 1961 个 chunk，重新构建 hybrid collection 成本低；同时实测 4 个 benchmark query 的 Recall@5=1.0，`source_filter` 覆盖六类来源。原始方案保留可以降低回退风险，并继续服务于 BM25 单独验证。

## 模块边界

本模块负责：

- 多来源知识采集与清洗
- 文档标准化、分块、元数据建模
- embedding 与向量入库
- BM25 索引
- 混合检索与 rerank
- 上下文拼装
- 检索评估与定时刷新任务

本模块不负责：

- 最终回答生成
- 前端展示
- 情绪分类
- 实时请求路径中的在线抓取

## 对外接口

```python
def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult:
    ...


def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
    ...


def index_documents(documents: list[dict], source: str) -> int:
    ...
```

`RetrievedDocument.metadata` 固定字段：

- `url`
- `published_at`
- `language`
- `source_id`
- `entity_tags`
- `ingested_at`

## 目录结构

```text
rag/
├── src/
│   ├── ingestion/
│   ├── indexing/
│   ├── retrieval/
│   ├── evaluation/
│   └── jobs/
├── data/
├── vectordb/
├── requirements.txt
└── README.md
```
