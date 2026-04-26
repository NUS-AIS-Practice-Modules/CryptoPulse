# CryptoPulse Chatbot 模块

**负责人**：Wei Yitao（E1458658）  
**模块角色**：系统集成层 — 将 NER、情感分析、RAG、LLM 组合成统一的 REST API 服务

---

## 模块架构

```
用户消息
    ↓
POST /api/chat
    ↓
1. NER 实体提取      → 识别 "Bitcoin" → BTC（规范化为 ticker）
2. 情感缓存查询      → lookup("BTC") → Bullish 60% / Bearish 25% / Neutral 15%
3. RAG 知识检索      → 实体增强查询 → 背景知识文本
4. Prompt 组装       → 系统角色 + RAG上下文 + 情感数据 + 对话历史 + 用户消息
5. LLM 生成回复      → OpenAI gpt-4o-mini（或 LoRA generate_response）
    ↓
返回 reply + sentiment + entities + sources
```

### 依赖关系

```
Frontend ──HTTP──▶ Chatbot ──Python 函数──▶ RAG（知识检索）
                           ──读文件──▶ LoRA 产出的 sentiment_summary.json
                           ──内置──▶ NER（LLM-based 实体提取）
```

---

## 快速启动

### 1. 环境准备（首次）

```bash
cd chatbot
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. 启动服务（Mock 模式，无需 API Key）

```bash
USE_MOCK=true .venv/bin/uvicorn src.app:app --reload --port 8000
```

启动成功标志：
```
INFO  Loading sentiment cache: 6 cryptos from ./data/sentiment_summary.json
INFO  Uvicorn running on http://0.0.0.0:8000
```

### 3. 启动服务（真实模式）

在 `.env` 中填入真实 key：
```
USE_MOCK=false
OPENAI_API_KEY=sk-你的key
```

然后：
```bash
.venv/bin/uvicorn src.app:app --reload --port 8000
```

---

## API 端点

### `GET /api/health`

检查各子模块状态。

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "modules": {
    "lora": {"status": "mock", "model_loaded": false},
    "rag":  {"status": "mock", "documents_indexed": 0},
    "ner":  {"status": "ok",   "backend": "llm"}
  }
}
```

---

### `POST /api/chat`

主对话接口。接收用户消息，经过完整 NLP pipeline 后返回回复。

**请求：**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current Bitcoin outlook?",
    "conversation_id": "session-001",
    "options": {
      "include_sentiment": true,
      "include_sources": true
    }
  }'
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | string（必填） | 用户输入的问题 |
| `conversation_id` | string（可选） | 对话 ID，不传则自动生成，用于多轮对话 |
| `options.include_sentiment` | bool | 是否在响应中包含情感数据，默认 true |
| `options.include_sources` | bool | 是否包含 RAG 来源，默认 true |

**响应：**
```json
{
  "reply": "Based on current market analysis, Bitcoin (BTC) sentiment is bullish...",
  "sentiment": {
    "label": "Bullish",
    "confidence": 0.60,
    "breakdown": {"bullish": 0.60, "bearish": 0.25, "neutral": 0.15}
  },
  "entities": [
    {"text": "BTC", "type": "CRYPTO", "start": 25, "end": 32, "confidence": 0.99}
  ],
  "sources": [
    {"title": "Bitcoin Whitepaper", "relevance": 0.92, "snippet": "..."},
    {"title": "CoinGecko Market Overview", "relevance": 0.85, "snippet": "..."}
  ],
  "conversation_id": "session-001",
  "timestamp": "2026-04-21T10:30:00Z"
}
```

**多轮对话示例：**
```bash
# 第一轮
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Tell me about Bitcoin", "conversation_id": "my-session"}'

# 第二轮（chatbot 记住上一轮，最多保留 5 轮历史）
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What about Ethereum?", "conversation_id": "my-session"}'
```

---

### `GET /api/sentiment/summary`

返回指定币种的历史情感趋势，供前端仪表盘使用。

```bash
curl "http://localhost:8000/api/sentiment/summary?crypto=BTC&period=7d"
```

| 参数 | 可选值 |
|------|--------|
| `crypto` | BTC, ETH, SOL 等 ticker |
| `period` | `7d` / `30d` / `90d` |

```json
{
  "crypto": "BTC",
  "period": "7d",
  "overall_sentiment": "Bullish",
  "trend": [
    {"date": "2026-04-15", "bullish": 0.63, "bearish": 0.21, "neutral": 0.16},
    {"date": "2026-04-16", "bullish": 0.67, "bearish": 0.19, "neutral": 0.14}
  ],
  "top_topics": ["ETF approval", "Halving", "Institutional adoption"],
  "data_points_analyzed": 15234
}
```

---

## 内部 Pipeline 详解

### NER 实体提取

- **Mock 模式**：关键词匹配（bitcoin→BTC, ethereum→ETH 等）
- **真实模式**：调用 OpenAI gpt-4o-mini，JSON mode，规范化为 ticker symbol
- CRYPTO 类型实体用于情感缓存查询和 RAG 查询增强

### 情感数据来源

**不做实时推理**。LoRA 团队离线处理社交媒体评论后产出：

```
chatbot/data/sentiment_summary.json
```

格式：
```json
{
  "BTC": {"overall": "Bullish", "bullish": 0.60, "bearish": 0.25, "neutral": 0.15, "sample_count": 15234},
  "ETH": {"overall": "Neutral", "bullish": 0.38, "bearish": 0.35, "neutral": 0.27, "sample_count": 8901}
}
```

Chatbot 启动时加载到内存，查询为 O(1)。**LoRA 团队负责更新此文件。**

### RAG 检索

- 查询 = 用户原始消息 + NER 提取的 ticker（如 "Bitcoin outlook BTC"）
- 调用 `rag/src/retrieval.py` 的 `get_context_for_llm()` 函数
- Mock 模式返回固定的加密货币背景知识段落

### LLM 生成

| `LLM_BACKEND` | 调用方式 |
|--------------|---------|
| `openai`（默认） | OpenAI ChatCompletion API |
| `lora` | `lora/src/inference.py` 的 `generate_response()` |

---

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USE_MOCK` | `true` | true = 全部用 mock 数据，无需 API key |
| `NER_BACKEND` | `llm` | `llm`=OpenAI NER，`model`=BERTweet（待实现） |
| `LLM_BACKEND` | `openai` | `openai` 或 `lora` |
| `OPENAI_API_KEY` | — | OpenAI API key（USE_MOCK=false 时必填） |
| `OPENAI_NER_MODEL` | `gpt-4o-mini` | NER 用的模型 |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | 对话生成用的模型 |
| `MAX_HISTORY_TURNS` | `5` | 传给 LLM 的最大历史轮数 |
| `SENTIMENT_DATA_PATH` | `./data/sentiment_summary.json` | LoRA 团队产出的情感数据路径 |

---

## 运行测试

```bash
USE_MOCK=true .venv/bin/pytest tests/ -v
```

预期输出：17 passed

---

## 与其他模块的对接

### Chatbot 需要 LoRA 团队提供

`chatbot/data/sentiment_summary.json`，格式见上方「情感数据来源」。

### Chatbot 需要 RAG 团队提供

`rag/src/retrieval.py` 中的函数（接口已在 `docs/INTERFACES.md` 定义）：
```python
def get_context_for_llm(query: str, max_tokens: int = 2000, top_k: int = 5) -> str: ...
def retrieve(query: str, top_k: int = 5, source_filter: list[str] | None = None) -> RetrievalResult: ...
```

### Frontend 团队调用 Chatbot

所有接口 schema 见 `docs/INTERFACES.md`。Chatbot API 地址：`http://localhost:8000`。

---

## 交互式文档

服务启动后访问 `http://localhost:8000/docs`，可在浏览器中直接测试所有接口。
