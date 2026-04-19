# Frontend 模块架构

## 一句话概述

Frontend 模块负责提供 CryptoPulse 的 Web 用户界面，承担用户与系统交互入口，包括聊天问答、文件上传、消息展示，以及可选 Dashboard 数据可视化页面。

## 技术栈

- **框架**: React
- **语言**: TypeScript
- **样式方案**: Tailwind CSS
- **状态管理**: React Context + Hooks
- **图表库**: Recharts
- **HTTP 客户端**: Fetch API
- **构建工具**: Vite

## 页面结构

### 主聊天页面

```text
┌────────────────────────────────────────┐
│ Header                                 │
├──────────────┬─────────────────────────┤
│ Sidebar      │ Chat Area               │
│ - Chat       │ 消息列表                │
│ - Dashboard  │ 输入框                  │
│ - Settings   │ 上传按钮 + 发送按钮     │
└──────────────┴─────────────────────────┘
```

Sidebar:

- Chat 页面
- Dashboard 页面
- Settings（可选）

Chat Area:

- 消息列表（用户消息 / AI 消息）
- 输入框
- 文件上传按钮
- 发送按钮
- Loading 状态

### Dashboard 页面

- 情绪趋势折线图
- Bullish / Bearish / Neutral 分布图
- Top Topics
- 数据统计卡片

## 与后端交互

- `POST /api/chat`
- `GET /api/sentiment/summary`
- `GET /api/health`

文件上传能力预留给后续 RAG 文档分析流程，当前主要作为 UI 能力占位。

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React | 生态成熟，组件化开发方便 |
| 类型系统 | TypeScript | 类型安全，降低联调错误 |
| 样式方案 | Tailwind CSS | 开发效率高 |
| 状态管理 | Context + Hooks | 当前项目规模适中 |
| 图表库 | Recharts | 与 React 集成方便 |
| 构建工具 | Vite | 启动快，开发体验好 |

## 目录结构

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ChatBox.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── FileUpload.tsx
│   │   ├── Sidebar.tsx
│   │   └── Charts.tsx
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   └── DashboardPage.tsx
│   ├── services/
│   │   └── api.ts
│   ├── hooks/
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── vite.config.ts
```

## 模块边界

Frontend 负责：

- 页面展示
- 用户交互
- API 调用
- 前端状态管理

Frontend 不负责：

- AI 推理逻辑
- 情绪分析算法
- RAG 检索逻辑
- 数据库存储

