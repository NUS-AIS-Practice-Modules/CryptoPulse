import { buildMockReply, mockDashboardSummary, mockHealthStatus } from "../mock/data";
import type { ChatReply, DashboardSummary, HealthStatus } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";
export const runtimeConfig = {
  apiBaseUrl: API_BASE_URL,
  useMock: USE_MOCK,
  frontendMode: USE_MOCK ? "mock" : "real-api"
} as const;

interface ChatPayload {
  message: string;
  conversation_id?: string;
  file?: File | null;
}

interface ChatApiResponse {
  reply: string;
  conversation_id: string;
  sentiment?: {
    label?: "Bullish" | "Bearish" | "Neutral";
    confidence?: number;
    breakdown?: Record<string, number>;
  } | null;
  sources?: Array<{
    title?: string;
    url?: string;
    relevance?: number;
    snippet?: string;
  }>;
}

interface SentimentSummaryApiResponse {
  crypto: string;
  period: string;
  overall_sentiment: "Bullish" | "Bearish" | "Neutral";
  trend: Array<{
    date: string;
    bullish: number;
    bearish: number;
    neutral: number;
  }>;
  top_topics: string[];
  data_points_analyzed: number;
}

interface HealthApiResponse {
  status: "ok" | "degraded" | "down";
  modules?: Record<string, { status?: string; [key: string]: unknown }>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type") && !(options?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function sendChatMessage(payload: ChatPayload): Promise<ChatReply> {
  if (USE_MOCK) {
    await new Promise((resolve) => window.setTimeout(resolve, 900));
    return buildMockReply(payload.message, payload.conversation_id);
  }

  const body = JSON.stringify({
    message: payload.message,
    conversation_id: payload.conversation_id,
    options: {
      include_sentiment: true,
      include_sources: true
    }
  });

  const response = await request<ChatApiResponse>("/api/chat", {
    method: "POST",
    body
  });

  return {
    reply: response.reply,
    conversation_id: response.conversation_id,
    sentiment: response.sentiment?.label,
    sources: response.sources?.map((source, index) => ({
      title: source.title || `Source ${index + 1}`,
      url: source.url,
      relevance: source.relevance,
      snippet: source.snippet
    }))
  };
}

export async function getSentimentSummary(period = "7d", crypto = "BTC"): Promise<DashboardSummary> {
  if (USE_MOCK) {
    await new Promise((resolve) => window.setTimeout(resolve, 500));
    return mockDashboardSummary;
  }

  const params = new URLSearchParams({ crypto, period });
  const response = await request<SentimentSummaryApiResponse>(`/api/sentiment/summary?${params}`);
  const latest = response.trend[response.trend.length - 1] || { bullish: 0, bearish: 0, neutral: 0 };

  return {
    totalAnalyses: response.data_points_analyzed,
    activeTopics: response.top_topics.length,
    health: "Healthy",
    lastUpdated: new Date().toLocaleString(),
    trend: response.trend,
    distribution: [
      { name: "Bullish", value: latest.bullish },
      { name: "Bearish", value: latest.bearish },
      { name: "Neutral", value: latest.neutral }
    ],
    topTopics: response.top_topics
  };
}

export async function getHealthStatus(): Promise<HealthStatus> {
  if (USE_MOCK) {
    await new Promise((resolve) => window.setTimeout(resolve, 300));
    return mockHealthStatus;
  }

  const response = await request<HealthApiResponse>("/api/health");
  const modules = response.modules || {};
  const moduleSummary = Object.entries(modules)
    .map(([name, module]) => `${name}: ${module.status || "unknown"}`)
    .join(", ");

  return {
    status: response.status,
    message: moduleSummary || "Health endpoint reachable.",
    frontendMode: runtimeConfig.frontendMode,
    apiBaseUrl: API_BASE_URL,
    modules
  };
}
