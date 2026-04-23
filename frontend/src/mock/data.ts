import type { ChatReply, DashboardSummary, HealthStatus } from "../types";

export const mockDashboardSummary: DashboardSummary = {
  totalAnalyses: 284,
  activeTopics: 12,
  health: "Healthy",
  lastUpdated: "2026-04-22 10:30",
  trend: [
    { date: "04-16", bullish: 28, bearish: 18, neutral: 12 },
    { date: "04-17", bullish: 32, bearish: 16, neutral: 15 },
    { date: "04-18", bullish: 36, bearish: 13, neutral: 11 },
    { date: "04-19", bullish: 24, bearish: 23, neutral: 14 },
    { date: "04-20", bullish: 42, bearish: 12, neutral: 10 },
    { date: "04-21", bullish: 39, bearish: 15, neutral: 16 },
    { date: "04-22", bullish: 44, bearish: 10, neutral: 13 }
  ],
  distribution: [
    { name: "Bullish", value: 56 },
    { name: "Bearish", value: 22 },
    { name: "Neutral", value: 22 }
  ],
  topTopics: ["BTC ETF flows", "ETH staking", "Macro rates", "Solana activity"]
};

export const mockHealthStatus: HealthStatus = {
  status: "ok",
  message: "All systems operational."
};

export function buildMockReply(message: string, conversationId?: string): ChatReply {
  const topic = message.trim() || "market sentiment";

  return {
    reply: `Mock analysis ready. Based on "${topic}", the current tone looks cautiously bullish, with stronger interest around momentum and ETF-related narratives.`,
    conversation_id: conversationId ?? "mock-conversation-001",
    sentiment: "Bullish",
    sources: [
      { title: "Internal Mock Feed", url: "https://example.com/mock-feed" },
      { title: "Sentiment Snapshot", url: "https://example.com/snapshot" }
    ]
  };
}
