import { useEffect, useState } from "react";
import { Charts } from "../components/Charts";
import { getSentimentSummary } from "../services/api";
import type { DashboardSummary } from "../types";

const timeRanges = [
  { key: "7d", label: "7 Days" },
  { key: "30d", label: "30 Days" },
  { key: "90d", label: "90 Days" }
] as const;

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState<(typeof timeRanges)[number]["key"]>("7d");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const summaryData = await getSentimentSummary(selectedRange);
        setSummary(summaryData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Dashboard failed to load");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [selectedRange]);

  return (
    <section className="flex h-full flex-col gap-5">
      <div className="flex flex-col gap-4 rounded-[32px] border border-white/70 bg-white/80 p-6 shadow-panel backdrop-blur lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Dashboard</p>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-ink">
            Sentiment overview and topic radar
          </h1>
          <p className="mt-3 max-w-2xl text-slate-600">
            Track sentiment trends, Bullish/Bearish/Neutral mix, top topics, and system health.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {timeRanges.map((range) => (
            <button
              key={range.key}
              type="button"
              onClick={() => setSelectedRange(range.key)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                selectedRange === range.key
                  ? "bg-ink text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="rounded-[28px] bg-white/80 p-8 text-slate-500 shadow-panel">Loading...</div>
      ) : error ? (
        <div className="rounded-[28px] bg-rose-50 p-8 text-rose-700 shadow-panel">{error}</div>
      ) : summary ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard title="Total Analyses" value={String(summary.totalAnalyses)} />
            <StatCard title="Overall Sentiment" value={summary.overallSentiment} />
            <StatCard title="Bullish Ratio" value={summary.bullishRatio} />
            <StatCard title="Trend Direction" value={summary.trendDirection} />
          </div>

          <Charts summary={summary} />

          <section className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-panel">
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Last Updated</p>
            <p className="mt-4 font-display text-3xl font-semibold text-ink">{summary.lastUpdated}</p>
            <p className="mt-3 text-slate-600">
              Showing sentiment data for the past {selectedRange}. Trend direction compares the second half of the period against the first.
            </p>
          </section>
        </>
      ) : null}
    </section>
  );
}

interface StatCardProps {
  title: string;
  value: string;
}

function StatCard({ title, value }: StatCardProps) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-white/85 p-5 shadow-panel">
      <p className="text-sm uppercase tracking-[0.24em] text-slate-500">{title}</p>
      <p className="mt-3 font-display text-3xl font-semibold text-ink">{value}</p>
    </article>
  );
}
