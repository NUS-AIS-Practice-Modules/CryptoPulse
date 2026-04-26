# Frontend API 接口文档

本文档面向 `CryptoPulse` 前端联调，基于当前参考文档与已实现的前端代码整理。

当前前端默认通过环境变量访问后端：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=true
```

- `VITE_API_BASE_URL`：后端服务地址
- `VITE_USE_MOCK`：是否使用本地 Mock 数据
- 当 `VITE_USE_MOCK=false` 时，前端会请求真实后端接口

---

## 1. 接口总览

| Method | Path | 用途 |
| --- | --- | --- |
| `POST` | `/api/chat` | 用户发送问题，获取 AI 回复、情绪标签与来源 |
| `GET` | `/api/sentiment/summary` | Dashboard 获取情绪趋势、分布和主题摘要 |
| `GET` | `/api/health` | 检查系统健康状态 |

默认拼接方式：

```text
{VITE_API_BASE_URL}{path}
```

示例：

```text
http://localhost:8000/api/chat
```

---

## 2. 通用约定

### 2.1 Content-Type

前端当前有两种请求方式：

- 当 `/api/chat` 不带文件上传时，使用 `application/json`
- 当 `/api/chat` 带文件上传时，使用 `multipart/form-data`
- `GET` 接口无需请求体

### 2.2 错误处理

前端当前的错误处理逻辑为：

- 如果 HTTP 状态码不是 `2xx`
- 前端会读取响应体文本
- 并将文本直接作为错误消息展示

因此建议后端在失败时返回清晰的纯文本，或返回可读性较高的错误说明。

建议状态码：

| 状态码 | 含义 |
| --- | --- |
| `200` | 请求成功 |
| `400` | 参数错误 |
| `413` | 上传文件过大 |
| `415` | 文件类型不支持 |
| `500` | 服务内部错误 |
| `503` | 模型/服务暂不可用 |

---

## 3. `POST /api/chat`

### 3.1 用途

用于聊天问答主流程：

- 发送用户问题
- 支持多轮会话
- 可选上传文档
- 返回 AI 回复
- 返回情绪标签与引用来源

### 3.2 请求格式

#### 场景 A：纯文本对话

`Content-Type: application/json`

请求体：

```json
{
  "message": "今天 BTC 市场情绪怎么样？",
  "conversation_id": "conv-001"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message` | `string` | 是 | 用户输入的问题 |
| `conversation_id` | `string` | 否 | 多轮对话 ID，首次对话可不传 |

#### 场景 B：带文件上传

`Content-Type: multipart/form-data`

表单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message` | `string` | 是 | 用户输入的问题 |
| `conversation_id` | `string` | 否 | 多轮对话 ID |
| `file` | `File` | 否 | 上传文档 |

当前前端支持选择的文件类型：

- `PDF`
- `TXT`
- `DOCX`

说明：

- 文件上传 UI 已实现
- 真实文件解析能力依赖后端
- 若后端暂不支持文件，可先忽略 `file` 字段并只处理文本消息

### 3.3 成功响应

```json
{
  "reply": "当前市场情绪偏谨慎乐观，ETF 相关叙事带动了 BTC 讨论热度。",
  "conversation_id": "conv-001",
  "sentiment": "Bullish",
  "sources": [
    {
      "title": "Market Snapshot",
      "url": "https://example.com/market-snapshot"
    }
  ]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `reply` | `string` | 是 | AI 回复内容 |
| `conversation_id` | `string` | 是 | 对话 ID，前端用于串联多轮会话 |
| `sentiment` | `"Bullish" \| "Bearish" \| "Neutral"` | 否 | 当前问题对应的情绪分析结果 |
| `sources` | `SourceLink[]` | 否 | 引用来源列表 |

`SourceLink` 结构：

```json
{
  "title": "Source title",
  "url": "https://example.com/source"
}
```

### 3.4 失败响应建议

纯文本示例：

```text
Invalid request: message is required.
```

或 JSON 示例：

```json
{
  "error": "Invalid request: message is required."
}
```

说明：

- 当前前端在失败时优先按文本读取响应体
- 若后端返回 JSON，建议同时确保可转成易读文本

---

## 4. `GET /api/sentiment/summary`

### 4.1 用途

用于 Dashboard 页面展示：

- 情绪趋势折线图
- Bullish / Bearish / Neutral 分布图
- Top Topics
- 汇总统计卡片

### 4.2 请求参数

当前前端尚未传递查询参数。

如果后续需要支持时间范围筛选，建议可扩展为：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `range` | `string` | 否 | 如 `7d` / `30d` / `90d` |

示例：

```text
/api/sentiment/summary?range=7d
```

### 4.3 成功响应

```json
{
  "totalAnalyses": 284,
  "activeTopics": 12,
  "health": "Healthy",
  "lastUpdated": "2026-04-22 10:30",
  "trend": [
    {
      "date": "04-16",
      "bullish": 28,
      "bearish": 18,
      "neutral": 12
    }
  ],
  "distribution": [
    {
      "name": "Bullish",
      "value": 56
    },
    {
      "name": "Bearish",
      "value": 22
    },
    {
      "name": "Neutral",
      "value": 22
    }
  ],
  "topTopics": ["BTC ETF flows", "ETH staking", "Macro rates"]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `totalAnalyses` | `number` | 是 | 已分析数据总量 |
| `activeTopics` | `number` | 是 | 当前活跃主题数 |
| `health` | `"Healthy" \| "Warning" \| "Offline"` | 是 | 系统整体健康标记 |
| `lastUpdated` | `string` | 是 | 最近更新时间 |
| `trend` | `TrendPoint[]` | 是 | 趋势图数据 |
| `distribution` | `SentimentDistribution[]` | 是 | 情绪占比数据 |
| `topTopics` | `string[]` | 是 | 热门主题列表 |

`TrendPoint` 结构：

```json
{
  "date": "04-16",
  "bullish": 28,
  "bearish": 18,
  "neutral": 12
}
```

`SentimentDistribution` 结构：

```json
{
  "name": "Bullish",
  "value": 56
}
```

---

## 5. `GET /api/health`

### 5.1 用途

用于检测系统可用性，并在 Dashboard 中展示 API 健康状态。

### 5.2 成功响应

```json
{
  "status": "ok",
  "message": "All systems operational."
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | `"ok" \| "degraded" \| "down"` | 是 | 系统状态 |
| `message` | `string` | 是 | 状态说明 |

---

## 6. TypeScript 类型对照

前端当前使用的核心类型如下。

### 6.1 `ChatReply`

```ts
interface ChatReply {
  reply: string;
  conversation_id: string;
  sentiment?: "Bullish" | "Bearish" | "Neutral";
  sources?: SourceLink[];
}
```

### 6.2 `DashboardSummary`

```ts
interface DashboardSummary {
  totalAnalyses: number;
  activeTopics: number;
  health: "Healthy" | "Warning" | "Offline";
  lastUpdated: string;
  trend: TrendPoint[];
  distribution: SentimentDistribution[];
  topTopics: string[];
}
```

### 6.3 `HealthStatus`

```ts
interface HealthStatus {
  status: "ok" | "degraded" | "down";
  message: string;
}
```

---

## 7. Mock 模式说明

当前前端支持本地 Mock 模式，适合后端尚未准备好时进行 UI 联调。

开启方式：

```env
VITE_USE_MOCK=true
```

Mock 覆盖接口：

- `POST /api/chat`
- `GET /api/sentiment/summary`
- `GET /api/health`

关闭方式：

```env
VITE_USE_MOCK=false
```

---

## 8. 后续扩展建议

建议后端后续预留以下能力：

1. `POST /api/chat` 支持流式输出，如 `SSE` 或 `WebSocket`
2. `GET /api/sentiment/summary` 支持 `range` 查询参数
3. 增加历史会话接口，如 `GET /api/conversations`
4. 增加文档上传/解析专用接口，如 `POST /api/files/upload`

