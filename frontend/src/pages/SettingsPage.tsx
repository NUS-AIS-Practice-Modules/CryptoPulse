import { runtimeConfig } from "../services/api";

export function SettingsPage() {
  return (
    <section className="grid gap-5">
      <div className="rounded-[32px] border border-white/70 bg-white/80 p-6 shadow-panel backdrop-blur">
        <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Settings</p>
        <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-ink">
          Environment and integration guide
        </h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          This page surfaces the current integration settings so the runtime mode is easy to confirm during development and recording.
        </p>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <InfoCard
          title="Local Setup"
          lines={[
            "Node.js >= 18",
            "npm.cmd install",
            "npm.cmd run dev",
            "Default URL: http://localhost:5173"
          ]}
        />
        <InfoCard
          title="Environment Variables"
          lines={[
            `VITE_API_BASE_URL=${runtimeConfig.apiBaseUrl}`,
            `VITE_USE_MOCK=${String(runtimeConfig.useMock)}`,
            `Frontend mode=${runtimeConfig.frontendMode}`,
            "These values come from the current Vite process. Restart npm run dev after changing environment variables."
          ]}
        />
        <InfoCard
          title="Available Endpoints"
          lines={["POST /api/chat", "GET /api/sentiment/summary", "GET /api/health"]}
        />
        <InfoCard
          title="Known Limits"
          lines={[
            "Conversation history persistence depends on backend support",
            "Streaming output can be extended with SSE or WebSocket later"
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
