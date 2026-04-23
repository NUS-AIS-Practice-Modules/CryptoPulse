# Frontend 环境搭建

## 前置要求

- Node.js >= 18
- npm >= 9

---

## 安装步骤

```bash
cd frontend
npm install

本地开发运行
npm run dev
默认地址：
http://localhost:5173

生产构建
npm run build

环境变量

创建 .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=true
说明：

VITE_API_BASE_URL：后端 API 地址
VITE_USE_MOCK：是否使用 Mock 数据

Mock 开发模式

后端未完成时使用本地 Mock 数据：

/api/chat
/api/sentiment/summary
/api/health

联调步骤
1. 启动后端 API 服务
2. 修改 .env.local
VITE_USE_MOCK=false
3. 启动前端
npm run dev
4. 测试聊天功能与 Dashboard 页面

当前限制
文件上传接口待后端完成
历史会话功能待后端支持
Streaming 输出后续可扩展 SSE / WebSocket