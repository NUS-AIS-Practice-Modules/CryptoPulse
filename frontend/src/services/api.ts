import { buildMockReply, mockDashboardSummary, mockHealthStatus } from "../mock/data";
import type { ChatReply, DashboardSummary, HealthStatus } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

interface ChatPayload {
  message: string;
  conversation_id?: string;
  file?: File | null;
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

  const body = payload.file
    ? (() => {
        const formData = new FormData();
        formData.append("message", payload.message);
        if (payload.conversation_id) {
          formData.append("conversation_id", payload.conversation_id);
        }
        formData.append("file", payload.file);
        return formData;
      })()
    : JSON.stringify(payload);

  return request<ChatReply>("/api/chat", {
    method: "POST",
    body
  });
}

export async function getSentimentSummary(): Promise<DashboardSummary> {
  if (USE_MOCK) {
    await new Promise((resolve) => window.setTimeout(resolve, 500));
    return mockDashboardSummary;
  }

  return request<DashboardSummary>("/api/sentiment/summary");
}

export async function getHealthStatus(): Promise<HealthStatus> {
  if (USE_MOCK) {
    await new Promise((resolve) => window.setTimeout(resolve, 300));
    return mockHealthStatus;
  }

  return request<HealthStatus>("/api/health");
}
