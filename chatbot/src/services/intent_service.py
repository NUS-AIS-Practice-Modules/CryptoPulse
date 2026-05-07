import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a query router for a cryptocurrency sentiment chatbot.
Analyze the user message and return a JSON object with these fields:

- needs_sentiment (bool): true if the user is asking about market sentiment, mood,
  bullish/bearish signals, or emotional market state
- needs_rag (bool): true if the question requires external knowledge about crypto news,
  events, prices, or technical details that a general LLM would not know
- sentiment_period ("7d"|"30d"|"90d"|null): time window if sentiment is needed;
  map "this week/recently/lately" → "7d", "this month/last month" → "30d",
  "last quarter/3 months" → "90d"; default to "7d" when period is unspecified
- sentiment_scope ("global"|"coin"|null): "global" if asking about overall crypto
  market, "coin" if asking about a specific cryptocurrency; null if no sentiment needed

Return ONLY valid JSON, no explanation."""

_EXAMPLES = [
    {"role": "user", "content": "What is the overall market sentiment this week?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_period":"7d","sentiment_scope":"global"}'},
    {"role": "user", "content": "How has market mood changed over the last month?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_period":"30d","sentiment_scope":"global"}'},
    {"role": "user", "content": "Tell me about Ethereum's technology"},
    {"role": "assistant", "content": '{"needs_sentiment":false,"needs_rag":true,"sentiment_period":null,"sentiment_scope":null}'},
    {"role": "user", "content": "Is Bitcoin bullish right now?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":true,"sentiment_period":"7d","sentiment_scope":"coin"}'},
    {"role": "user", "content": "Hello, what can you do?"},
    {"role": "assistant", "content": '{"needs_sentiment":false,"needs_rag":false,"sentiment_period":null,"sentiment_scope":null}'},
]


@dataclass
class Intent:
    needs_sentiment: bool
    needs_rag: bool
    sentiment_period: str | None   # "7d" | "30d" | "90d" | None
    sentiment_scope: str | None    # "global" | "coin" | None


_FALLBACK = Intent(needs_sentiment=True, needs_rag=True, sentiment_period="7d", sentiment_scope="global")


def classify_intent(message: str, api_key: str, model: str) -> Intent:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                *_EXAMPLES,
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=80,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return Intent(
            needs_sentiment=bool(data.get("needs_sentiment", True)),
            needs_rag=bool(data.get("needs_rag", True)),
            sentiment_period=data.get("sentiment_period"),
            sentiment_scope=data.get("sentiment_scope"),
        )
    except Exception as e:
        logger.warning("Intent classification failed (%s) — using fallback", e)
        return _FALLBACK
