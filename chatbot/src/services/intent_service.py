import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a query router for a cryptocurrency sentiment chatbot.
Today's date is {today}.

Analyze the user message and return a JSON object with these fields:

- needs_sentiment (bool): true if the user is asking about market sentiment, mood,
  bullish/bearish signals, or emotional market state
- needs_rag (bool): true if the question requires external knowledge about crypto news,
  events, prices, or technical details that a general LLM would not know
- sentiment_scope ("global"|"coin"|null): "global" if asking about overall crypto
  market, "coin" if asking about a specific cryptocurrency; null if no sentiment needed
- sentiment_days (int|null): for relative time expressions, return the number of days
  only (e.g. "this week" → 7, "last month" → 30, "last 40 days" → 40,
  "last quarter" → 90); null when an explicit date range is given or no sentiment needed
- date_range ({{"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}}|null): ONLY for explicit date
  ranges like "from 3.13 to 4.5" or "between Feb 20 and March 12"; resolve partial
  dates using today's year; null when sentiment_days is set or no sentiment needed

Return ONLY valid JSON, no explanation."""

_EXAMPLES = [
    {"role": "user", "content": "What is the overall market sentiment this week?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":7,"date_range":null}'},
    {"role": "user", "content": "How has market mood changed over the last month?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":30,"date_range":null}'},
    {"role": "user", "content": "Show me market mood over the last 40 days"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":40,"date_range":null}'},
    {"role": "user", "content": "How has crypto sentiment trended over the past 3 months?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":90,"date_range":null}'},
    {"role": "user", "content": "What is the sentiment from 3.13 to 4.5?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":null,"date_range":{"start":"2026-03-13","end":"2026-04-05"}}'},
    {"role": "user", "content": "How was the crypto market between Feb 20 and March 12?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":null,"date_range":{"start":"2026-02-20","end":"2026-03-12"}}'},
    {"role": "user", "content": "Is Bitcoin bullish right now?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":true,"sentiment_scope":"coin","sentiment_days":7,"date_range":null}'},
    {"role": "user", "content": "Tell me about Ethereum's technology"},
    {"role": "assistant", "content": '{"needs_sentiment":false,"needs_rag":true,"sentiment_scope":null,"sentiment_days":null,"date_range":null}'},
    {"role": "user", "content": "Hello, what can you do?"},
    {"role": "assistant", "content": '{"needs_sentiment":false,"needs_rag":false,"sentiment_scope":null,"sentiment_days":null,"date_range":null}'},
]


@dataclass
class Intent:
    needs_sentiment: bool
    needs_rag: bool
    sentiment_scope: str | None
    date_range: dict | None        # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} | None


def _days_to_range(days: int) -> dict:
    today = date.today()
    return {
        "start": (today - timedelta(days=days - 1)).isoformat(),
        "end": today.isoformat(),
    }


_FALLBACK = Intent(needs_sentiment=True, needs_rag=True, sentiment_scope="global", date_range=_days_to_range(7))


def classify_intent(message: str, api_key: str, model: str) -> Intent:
    today = date.today().isoformat()
    system = _SYSTEM_PROMPT.format(today=today)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                *_EXAMPLES,
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=100,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        # Python computes the date range from days — no LLM arithmetic needed
        sentiment_days = data.get("sentiment_days")
        if sentiment_days:
            date_range = _days_to_range(int(sentiment_days))
        else:
            date_range = data.get("date_range")

        return Intent(
            needs_sentiment=bool(data.get("needs_sentiment", True)),
            needs_rag=bool(data.get("needs_rag", True)),
            sentiment_scope=data.get("sentiment_scope"),
            date_range=date_range,
        )
    except Exception as e:
        logger.warning("Intent classification failed (%s) — using fallback", e)
        return _FALLBACK
