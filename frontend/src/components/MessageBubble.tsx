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
              <div className="mt-2 space-y-2">
                <p className="font-medium text-slate-600">Sources</p>
                {message.sources.map((source, index) => (
                  <div key={`${source.title}-${index}`} className="rounded-xl bg-slate-50 px-3 py-2">
                    {source.url ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-slate-700 transition hover:text-skyline"
                      >
                        {source.title}
                      </a>
                    ) : (
                      <p className="font-medium text-slate-700">{source.title}</p>
                    )}
                    {source.snippet ? (
                      <p className="mt-1 line-clamp-2 text-slate-500">{source.snippet}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
