# RAG 模块架构

## 一句话概述

基于 `Milvus + BAAI/bge-m3 + BM25 + reranker` 构建加密货币领域 RAG 模块，覆盖白皮书、监管文件、研究报告、历史案例、实时新闻与社媒内容，为 Chatbot 提供可控、可解释的上下文增强能力。

## 技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| 向量数据库 | Milvus | 支持大规模向量索引、过滤与持久化 |
| 嵌入模型 | `BAAI/bge-m3` | 适配新闻、报告、问答与多类型文本 |
| 分块策略 | 语义优先 + 固定窗口兜底 | 平衡上下文完整性和检索效率 |
| 关键词检索 | BM25 | 覆盖精确匹配场景 |
| 融合策略 | RRF | dense / sparse 融合稳定 |
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
dense retrieval + BM25 retrieval
   ↓
Reciprocal Rank Fusion
   ↓
cross-encoder reranker
   ↓
top-k documents
   ↓
context assembly
   ↓
get_context_for_llm()
```

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

