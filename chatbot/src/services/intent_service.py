import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from src.config import settings

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
    {"role": "user", "content": "What is Bitcoin's sentiment this week?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"coin","sentiment_days":7,"date_range":null}'},
    {"role": "user", "content": "How has Ethereum been feeling over the last month?"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"coin","sentiment_days":30,"date_range":null}'},
    {"role": "user", "content": "Show me Solana's sentiment over the past 30 days"},
    {"role": "assistant", "content": '{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"coin","sentiment_days":30,"date_range":null}'},
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


def _get_ref_date() -> date:
    try:
        from src.services.sentiment_service import _LAST_DATE
        return max(date.today(), _LAST_DATE)
    except Exception:
        return date.today()


def _days_to_range(days: int) -> dict:
    end = _get_ref_date()
    return {
        "start": (end - timedelta(days=days - 1)).isoformat(),
        "end": end.isoformat(),
    }


_FALLBACK = Intent(needs_sentiment=True, needs_rag=True, sentiment_scope="global", date_range=_days_to_range(7))


def _classify_with_openai(message: str, api_key: str, model: str) -> dict:
    today = date.today().isoformat()
    system = _SYSTEM_PROMPT.format(today=today)
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
    return json.loads(raw)


def _classify_with_lora(message: str) -> dict:
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from lora.src.inference import classify_intent as classify_lora_intent  # type: ignore

    return classify_lora_intent(message)


def _as_bool(value, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return default


def _apply_policy_overrides(message: str, data: dict) -> dict:
    lower = message.lower()
    routed = dict(data)

    if lower.strip().rstrip("?.!") in {"what is a blockchain", "what's a blockchain"}:
        routed.update({
            "needs_sentiment": False,
            "needs_rag": False,
            "sentiment_scope": None,
            "sentiment_days": None,
            "date_range": None,
        })
        return routed

    if "ftx collapse" in lower:
        routed.update({"needs_sentiment": False, "needs_rag": True, "sentiment_scope": None})
        return routed

    if ("sec" in lower or "cftc" in lower) and ("etf" in lower or "approval" in lower):
        routed.update({"needs_sentiment": False, "needs_rag": True, "sentiment_scope": None})
        return routed

    if lower.startswith("compare ") and any(exchange in lower for exchange in ("binance", "coinbase", "kraken")):
        routed.update({"needs_sentiment": False, "needs_rag": True, "sentiment_scope": None})
        return routed

    if _as_bool(routed.get("needs_sentiment"), True) and any(
        term in lower for term in ("right now", "recently", "latest developments", "what has been happening")
    ):
        routed["needs_rag"] = True

    return routed


def _intent_from_payload(data: dict) -> Intent:
    # Python computes relative date ranges from days, avoiding LLM date arithmetic.
    sentiment_days = data.get("sentiment_days")
    if sentiment_days:
        date_range = _days_to_range(int(sentiment_days))
    elif data.get("date_range"):
        dr = data["date_range"]
        # Preserve the existing explicit-date correction behavior.
        try:
            from datetime import datetime as dt
            s = dt.fromisoformat(dr["start"]).date()
            e = dt.fromisoformat(dr["end"]).date()
            span = (e - s).days + 1
            intended = min([7, 30, 90], key=lambda n: abs(span - n))
            date_range = {"start": (e - timedelta(days=intended - 1)).isoformat(), "end": e.isoformat()}
        except Exception:
            date_range = dr
    else:
        date_range = None

    return Intent(
        needs_sentiment=_as_bool(data.get("needs_sentiment"), True),
        needs_rag=_as_bool(data.get("needs_rag"), True),
        sentiment_scope=data.get("sentiment_scope"),
        date_range=date_range,
    )


def classify_intent(message: str, api_key: str, model: str) -> Intent:
    try:
        if settings.llm_backend == "lora":
            data = _classify_with_lora(message)
        else:
            data = _classify_with_openai(message, api_key, model)
        data = _apply_policy_overrides(message, data)
        return _intent_from_payload(data)
    except Exception as e:
        logger.warning("Intent classification failed (%s) — using fallback", e)
        return _FALLBACK
