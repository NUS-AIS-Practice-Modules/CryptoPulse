import type { ChatMessage } from "../types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-[24px] px-4 py-3 shadow-sm md:max-w-[70%] ${
          isUser
            ? "bg-skyline text-white"
            : isSystem
              ? "bg-amber-100 text-amber-950"
              : "bg-white text-slate-800"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>

        {(message.sentiment || message.sources?.length) && (
          <div className="mt-3 border-t border-slate-200/70 pt-3 text-xs text-slate-500">
            {message.sentiment ? <p>Sentiment: {message.sentiment}</p> : null}
            {message.sources?.length ? (
              <div className="mt-2 flex flex-wrap gap-2">
                {message.sources.map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full bg-slate-100 px-3 py-1 text-slate-700 transition hover:bg-slate-200"
                  >
                    {source.title}
                  </a>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
