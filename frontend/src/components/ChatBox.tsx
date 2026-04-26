import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

interface ChatBoxProps {
  messages: ChatMessage[];
  loading: boolean;
}

export function ChatBox({ messages, loading }: ChatBoxProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }, [messages, loading]);

  return (
    <div
      ref={containerRef}
      className="scrollbar-thin flex min-h-[360px] flex-1 flex-col gap-4 overflow-y-auto rounded-[28px] border border-white/70 bg-white/80 p-4 shadow-panel backdrop-blur"
    >
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {loading ? (
        <div className="flex justify-start">
          <div className="rounded-[24px] bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
            AI 正在分析中...
          </div>
        </div>
      ) : null}
    </div>
  );
}
