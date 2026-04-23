import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { DashboardSummary } from "../types";

interface ChartsProps {
  summary: DashboardSummary;
}

const COLORS = ["#1d4ed8", "#c2410c", "#0f766e"];

export function Charts({ summary }: ChartsProps) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
      <section className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-panel">
        <div className="mb-5">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Trend</p>
          <h3 className="font-display text-2xl font-semibold text-ink">Sentiment Timeline</h3>
        </div>
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={summary.trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 12 }} />
              <YAxis tick={{ fill: "#475569", fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="bullish" stroke="#1d4ed8" strokeWidth={3} />
              <Line type="monotone" dataKey="bearish" stroke="#c2410c" strokeWidth={3} />
              <Line type="monotone" dataKey="neutral" stroke="#0f766e" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-panel">
        <div className="mb-5">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Distribution</p>
          <h3 className="font-display text-2xl font-semibold text-ink">Market Tone Mix</h3>
        </div>
        <div className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={summary.distribution}
                dataKey="value"
                nameKey="name"
                innerRadius={65}
                outerRadius={100}
                paddingAngle={4}
              >
                {summary.distribution.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
