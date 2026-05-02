import { FormEvent, useState } from "react";
import { ChatBox } from "../components/ChatBox";
import { sendChatMessage } from "../services/api";
import type { ChatMessage } from "../types";

const STORAGE_KEYS = {
  conversationId: "cryptopulse.chat.conversation_id",
  messages: "cryptopulse.chat.messages"
} as const;

function createMessage(
  role: ChatMessage["role"],
  content: string,
  extra?: Partial<ChatMessage>
): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
    ...extra
  };
}

const initialMessages: ChatMessage[] = [
  createMessage(
    "assistant",
    "Welcome to CryptoPulse. Ask about market sentiment or open the Dashboard for the broader trend view."
  )
];

function loadStoredMessages(): ChatMessage[] {
  try {
    const storedMessages = window.localStorage.getItem(STORAGE_KEYS.messages);
    if (!storedMessages) {
      return initialMessages;
    }

    const parsed = JSON.parse(storedMessages);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : initialMessages;
  } catch {
    return initialMessages;
  }
}

function loadStoredConversationId(): string | undefined {
  return window.localStorage.getItem(STORAGE_KEYS.conversationId) || undefined;
}

function persistConversation(nextMessages: ChatMessage[], nextConversationId?: string) {
  window.localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(nextMessages));
  if (nextConversationId) {
    window.localStorage.setItem(STORAGE_KEYS.conversationId, nextConversationId);
  } else {
    window.localStorage.removeItem(STORAGE_KEYS.conversationId);
  }
}

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadStoredMessages);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(loadStoredConversationId);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || loading) {
      return;
    }

    const userMessage = createMessage("user", message);
    const pendingMessages = [...messages, userMessage];
    setMessages(pendingMessages);
    persistConversation(pendingMessages, conversationId);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendChatMessage({
        message,
        conversation_id: conversationId
      });

      const assistantMessage = createMessage("assistant", reply.reply, {
        sentiment: reply.sentiment,
        sources: reply.sources
      });
      const nextMessages = [...pendingMessages, assistantMessage];
      setConversationId(reply.conversation_id);
      setMessages(nextMessages);
      persistConversation(nextMessages, reply.conversation_id);
    } catch (error) {
      const messageText =
        error instanceof Error ? error.message : "Request failed. Check the backend service or switch to mock mode.";
      const nextMessages = [...pendingMessages, createMessage("system", messageText)];
      setMessages(nextMessages);
      persistConversation(nextMessages, conversationId);
    } finally {
      setLoading(false);
    }
  }

  function handleNewConversation() {
    setMessages(initialMessages);
    setConversationId(undefined);
    persistConversation(initialMessages);
  }

  return (
    <section className="flex h-full min-h-0 flex-col gap-5">
      <div className="shrink-0 rounded-[32px] border border-white/60 bg-hero-grid bg-white/65 p-6 shadow-panel backdrop-blur">
        <p className="text-sm uppercase tracking-[0.28em] text-slate-500">AI Workspace</p>
        <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl font-bold tracking-tight text-ink">
              Crypto chat with live sentiment context
            </h1>
            <p className="mt-3 max-w-2xl text-slate-600">
              The main chat flow supports multi-turn context, loading states, and error handling.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="rounded-2xl bg-white/80 px-4 py-3 text-sm text-slate-600 shadow-sm">
              Conversation ID: {conversationId ?? "Not created"}
            </div>
            <button
              type="button"
              onClick={handleNewConversation}
              disabled={loading}
              className="rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-skyline hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
            >
              New conversation
            </button>
          </div>
        </div>
      </div>

      <ChatBox messages={messages} loading={loading} />

      <form
        onSubmit={handleSubmit}
        className="shrink-0 rounded-[24px] border border-white/70 bg-white/80 p-3 shadow-panel backdrop-blur"
      >
        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask me: Is the market bullish or bearish today? What are the key themes?"
            rows={2}
            className="max-h-28 min-h-[72px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-skyline focus:bg-white"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-2xl bg-ink px-6 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 lg:w-[180px]"
          >
            {loading ? "Analyzing..." : "Send message"}
          </button>
        </div>
      </form>
    </section>
  );
}
