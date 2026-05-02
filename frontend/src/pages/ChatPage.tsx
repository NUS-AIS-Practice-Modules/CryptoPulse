import { FormEvent, useState } from "react";
import { ChatBox } from "../components/ChatBox";
import { FileUpload } from "../components/FileUpload";
import { sendChatMessage } from "../services/api";
import type { ChatMessage } from "../types";

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
    "Welcome to CryptoPulse. Ask about market sentiment, upload documents, or open the Dashboard for the broader trend view."
  )
];

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = input.trim();
    if (!message || loading) {
      return;
    }

    const userMessage = createMessage("user", message);
    setMessages((current) => [...current, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const reply = await sendChatMessage({
        message,
        conversation_id: conversationId,
        file: selectedFile
      });

      setConversationId(reply.conversation_id);
      setMessages((current) => [
        ...current,
        createMessage("assistant", reply.reply, {
          sentiment: reply.sentiment,
          sources: reply.sources
        })
      ]);
    } catch (error) {
      const messageText =
        error instanceof Error ? error.message : "Request failed. Check the backend service or switch to mock mode.";
      setMessages((current) => [...current, createMessage("system", messageText)]);
    } finally {
      setLoading(false);
    }
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
              The main chat flow supports multi-turn context, loading states, error handling, and a reserved file-upload control.
            </p>
          </div>
          <div className="rounded-2xl bg-white/80 px-4 py-3 text-sm text-slate-600 shadow-sm">
            Conversation ID: {conversationId ?? "Not created"}
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
          <div className="flex flex-col gap-3 lg:w-[260px]">
            <FileUpload file={selectedFile} onChange={setSelectedFile} />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-2xl bg-ink px-4 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Send message"}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
