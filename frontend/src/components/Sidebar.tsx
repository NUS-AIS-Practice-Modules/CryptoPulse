import type { ViewKey } from "../types";

interface SidebarProps {
  activeView: ViewKey;
  onChangeView: (view: ViewKey) => void;
}

const items: Array<{ key: ViewKey; label: string; description: string }> = [
  { key: "chat", label: "Chat", description: "对话、提问、上传文档" },
  { key: "dashboard", label: "Dashboard", description: "情绪分析和趋势总览" },
  { key: "settings", label: "Settings", description: "环境和联调说明" }
];

export function Sidebar({ activeView, onChangeView }: SidebarProps) {
  return (
    <aside className="flex h-full flex-col rounded-[28px] bg-ink px-5 py-6 text-white shadow-panel">
      <div>
        <p className="font-display text-2xl font-bold tracking-tight">CryptoPulse</p>
        <p className="mt-2 text-sm text-slate-300">
          一个面向加密市场舆情与问答的前端工作台。
        </p>
      </div>

      <nav className="mt-8 flex flex-1 flex-col gap-3">
        {items.map((item) => {
          const active = item.key === activeView;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onChangeView(item.key)}
              className={`rounded-2xl border px-4 py-4 text-left transition ${
                active
                  ? "border-white/30 bg-white/15"
                  : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
              }`}
            >
              <span className="block text-base font-semibold">{item.label}</span>
              <span className="mt-1 block text-sm text-slate-300">{item.description}</span>
            </button>
          );
        })}
      </nav>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
        <p className="font-medium text-white">模式切换</p>
        <p className="mt-1">录屏模式使用真实后端；需要离线演示时可在 `.env.local` 切换 mock。</p>
      </div>
    </aside>
  );
}
