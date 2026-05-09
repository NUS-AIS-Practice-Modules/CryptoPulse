export type ViewKey = "chat" | "dashboard" | "settings";

export type Sender = "user" | "assistant" | "system";

export interface SourceLink {
  title: string;
  url?: string;
  relevance?: number;
  snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: Sender;
  content: string;
  createdAt: string;
  sentiment?: "Bullish" | "Bearish" | "Neutral";
  sources?: SourceLink[];
}

export interface ChatReply {
  reply: string;
  conversation_id: string;
  sentiment?: "Bullish" | "Bearish" | "Neutral";
  sources?: SourceLink[];
}

export interface TrendPoint {
  date: string;
  bullish: number;
  bearish: number;
  neutral: number;
}

export interface SentimentDistribution {
  name: "Bullish" | "Bearish" | "Neutral";
  value: number;
}

export interface DashboardSummary {
  totalAnalyses: number;
  overallSentiment: "Bullish" | "Bearish" | "Neutral";
  bullishRatio: string;
  trendDirection: "Rising" | "Falling" | "Stable";
  lastUpdated: string;
  trend: TrendPoint[];
  distribution: SentimentDistribution[];
}

export interface HealthStatus {
  status: "ok" | "degraded" | "down";
  message: string;
  frontendMode: "mock" | "real-api";
  apiBaseUrl: string;
  modules?: Record<string, unknown>;
}
