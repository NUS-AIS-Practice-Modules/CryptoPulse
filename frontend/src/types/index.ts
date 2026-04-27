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
  activeTopics: number;
  health: "Healthy" | "Warning" | "Offline";
  lastUpdated: string;
  trend: TrendPoint[];
  distribution: SentimentDistribution[];
  topTopics: string[];
}

export interface HealthStatus {
  status: "ok" | "degraded" | "down";
  message: string;
  modules?: Record<string, unknown>;
}
