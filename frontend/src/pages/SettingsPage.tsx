export function SettingsPage() {
  return (
    <section className="grid gap-5">
      <div className="rounded-[32px] border border-white/70 bg-white/80 p-6 shadow-panel backdrop-blur">
        <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Settings</p>
        <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-ink">
          Environment and integration guide
        </h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          这里把 `SETUP.md` 里的联调约定直接落成页面说明，方便开发和演示时快速确认当前模式。
        </p>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <InfoCard
          title="Local Setup"
          lines={[
            "Node.js >= 18",
            "npm.cmd install",
            "npm.cmd run dev",
            "默认地址: http://localhost:5173"
          ]}
        />
        <InfoCard
          title="Environment Variables"
          lines={[
            "VITE_API_BASE_URL=http://localhost:8000",
            "VITE_USE_MOCK=true",
            "后端就绪后将 VITE_USE_MOCK 改为 false"
          ]}
        />
        <InfoCard
          title="Available Endpoints"
          lines={["POST /api/chat", "GET /api/sentiment/summary", "GET /api/health"]}
        />
        <InfoCard
          title="Known Limits"
          lines={[
            "文件上传接口目前仅预留 UI",
            "历史会话等待后端支持",
            "流式输出可后续扩展为 SSE / WebSocket"
          ]}
        />
      </div>
    </section>
  );
}

interface InfoCardProps {
  title: string;
  lines: string[];
}

function InfoCard({ title, lines }: InfoCardProps) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-panel">
      <p className="font-display text-2xl font-semibold text-ink">{title}</p>
      <div className="mt-4 space-y-3 text-slate-600">
        {lines.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
    </article>
  );
}
