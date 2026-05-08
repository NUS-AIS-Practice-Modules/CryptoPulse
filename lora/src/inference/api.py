import os
import re
import sys
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from shared.types import GenerationResult, SentimentResult


BULLISH_TERMS = {
    "approve",
    "approved",
    "approval",
    "bull",
    "bullish",
    "breakout",
    "gain",
    "gains",
    "inflows",
    "moon",
    "pump",
    "pumping",
    "rally",
    "rallying",
    "up",
}

BEARISH_TERMS = {
    "bear",
    "bearish",
    "crash",
    "decline",
    "down",
    "drop",
    "hack",
    "loss",
    "plunge",
    "selloff",
}


def _mock_enabled() -> bool:
    return os.getenv("LORA_USE_MOCK", "true").lower() != "false"


def _remote_base_url() -> str:
    return os.getenv("LORA_REMOTE_BASE_URL", "").rstrip("/")


def _sentiment_model() -> str:
    return os.getenv("LORA_SENTIMENT_MODEL", "sentiment-lora")


def _chat_model() -> str:
    return os.getenv("LORA_CHAT_MODEL", "ift-lora")


def _remote_timeout() -> float:
    raw = os.getenv("LORA_REMOTE_TIMEOUT_SECONDS", "30")
    try:
        return float(raw)
    except ValueError:
        return 30.0


def _post_remote(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = _remote_base_url()
    if not base_url:
        raise RuntimeError("LORA_REMOTE_BASE_URL is not configured")

    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("LORA_REMOTE_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(f"{base_url}{path}", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=_remote_timeout()) as response:
            if response.status >= 400:
                raise RuntimeError(f"AutoDL LoRA endpoint returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"AutoDL LoRA endpoint unavailable: {exc}") from exc


def _chat_completion(model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    response = _post_remote(
        "/chat/completions",
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )
    try:
        return str(response["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("AutoDL LoRA response did not match OpenAI chat completion shape") from exc


def _real_mode_unavailable() -> None:
    model_path = os.getenv("LORA_MODEL_PATH", "")
    if _remote_base_url():
        return
    if not model_path:
        raise RuntimeError(
            "LORA_USE_MOCK=false requires LORA_REMOTE_BASE_URL for the AutoDL service "
            "or LORA_MODEL_PATH for a local model runtime"
        )
    if not Path(model_path).exists():
        raise RuntimeError(f"LORA_MODEL_PATH does not exist: {model_path}")
    raise RuntimeError(
        "Local real LoRA inference runtime is not wired yet; set LORA_REMOTE_BASE_URL "
        "for the AutoDL deployment or use LORA_USE_MOCK=true for harness integration"
    )


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z]+", text.lower()))


def _normalize_label(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"bull", "bullish", "positive"}:
        return "Bullish"
    if value in {"bear", "bearish", "negative"}:
        return "Bearish"
    return "Neutral"


def _default_scores(label: str, confidence: float) -> dict[str, float]:
    confidence = max(0.0, min(1.0, confidence))
    remainder = max(0.0, 1.0 - confidence)
    if label == "Bullish":
        return {"bullish": confidence, "bearish": remainder / 2, "neutral": remainder / 2}
    if label == "Bearish":
        return {"bullish": remainder / 2, "bearish": confidence, "neutral": remainder / 2}
    return {"bullish": remainder / 2, "bearish": remainder / 2, "neutral": confidence}


def _normalize_scores(raw_scores: Any, label: str, confidence: float) -> dict[str, float]:
    if not isinstance(raw_scores, dict):
        return _default_scores(label, confidence)

    scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
    for key, value in raw_scores.items():
        normalized_key = str(key).strip().lower()
        if normalized_key in scores:
            try:
                scores[normalized_key] = float(value)
            except (TypeError, ValueError):
                continue
    return scores


def _sentiment_from_text(text: str) -> SentimentResult:
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        try:
            payload = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            payload = None

    if isinstance(payload, dict):
        raw_label = str(payload.get("label") or payload.get("sentiment") or "")
        label = _normalize_label(raw_label)
        try:
            confidence = float(payload.get("confidence", max(_default_scores(label, 0.6).values())))
        except (TypeError, ValueError):
            confidence = 0.6
        raw_scores = payload.get("scores") or payload.get("breakdown")
        return SentimentResult(
            label=label,
            confidence=max(0.0, min(1.0, confidence)),
            scores=_normalize_scores(raw_scores, label, confidence),
        )

    return _lexical_sentiment(content)


_INTENT_FALLBACK = {
    "needs_sentiment": True,
    "needs_rag": True,
    "sentiment_scope": "global",
    "sentiment_days": 7,
    "date_range": None,
}

_INTENT_SYSTEM_PROMPT = """You are a query router for a cryptocurrency sentiment chatbot.
Return exactly one JSON object for the current user message only, with these keys:
- needs_sentiment: boolean
- needs_rag: boolean
- sentiment_scope: "global", "coin", or null
- sentiment_days: integer or null
- date_range: {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"} or null
Rules:
- Technology or explanation questions need RAG and do not need sentiment.
- Greetings need neither sentiment nor RAG.
- Coin sentiment questions use sentiment_scope "coin".
Examples:
User: What is Bitcoin sentiment this week?
Assistant: {"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"coin","sentiment_days":7,"date_range":null}
User: Tell me about Ethereum technology
Assistant: {"needs_sentiment":false,"needs_rag":true,"sentiment_scope":null,"sentiment_days":null,"date_range":null}
User: Hello
Assistant: {"needs_sentiment":false,"needs_rag":false,"sentiment_scope":null,"sentiment_days":null,"date_range":null}
Do not include markdown, explanation, or additional examples."""


def _extract_json_object(text: str) -> dict[str, Any] | None:
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)

    decoder = json.JSONDecoder()
    try:
        payload, _ = decoder.raw_decode(content)
    except json.JSONDecodeError:
        payload = None
        for match in re.finditer(r"\{", content):
            try:
                payload, _ = decoder.raw_decode(content[match.start():])
                break
            except json.JSONDecodeError:
                continue
    return payload if isinstance(payload, dict) else None


def _coerce_key_value(raw: str) -> Any:
    value = raw.strip().strip(",")
    if value.startswith("{"):
        nested = _extract_json_object(value)
        if nested is not None:
            return nested

    unquoted = value.strip().strip('"').strip("'")
    normalized = unquoted.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    if normalized in {"null", "none", ""}:
        return None
    try:
        return int(unquoted)
    except ValueError:
        return unquoted


def _extract_key_value_object(text: str) -> dict[str, Any] | None:
    content = text.strip()
    keys = ["needs_sentiment", "needs_rag", "sentiment_scope", "sentiment_days", "date_range"]
    pattern = re.compile(r"\b(" + "|".join(keys) + r")\s*:")
    matches = list(pattern.finditer(content))
    if not matches:
        return None

    payload: dict[str, Any] = {}
    for index, match in enumerate(matches):
        key = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        payload[key] = _coerce_key_value(content[match.end():end])
    return payload


def _normalize_nullable_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"", "none", "null"}:
        return None
    return normalized


def _as_bool(value: Any, default: bool = True) -> bool:
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


def _intent_from_text(text: str) -> dict[str, Any]:
    payload = _extract_json_object(text) or _extract_key_value_object(text)
    if not payload:
        return dict(_INTENT_FALLBACK)

    scope = _normalize_nullable_string(payload.get("sentiment_scope"))
    if scope not in {"global", "coin", None}:
        scope = None

    sentiment_days = payload.get("sentiment_days")
    if sentiment_days in {"", "null", "none"}:
        sentiment_days = None
    elif sentiment_days is not None:
        try:
            sentiment_days = int(sentiment_days)
        except (TypeError, ValueError):
            sentiment_days = None

    date_range = payload.get("date_range")
    if not isinstance(date_range, dict) or not date_range.get("start") or not date_range.get("end"):
        date_range = None

    return {
        "needs_sentiment": _as_bool(payload.get("needs_sentiment"), True),
        "needs_rag": _as_bool(payload.get("needs_rag"), True),
        "sentiment_scope": scope,
        "sentiment_days": sentiment_days,
        "date_range": date_range,
    }


def _mock_intent(prompt: str) -> dict[str, Any]:
    text = prompt.lower()
    coin_terms = {
        "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
        "dogecoin", "doge", "shib", "xrp", "bnb", "ada",
    }
    asks_sentiment = any(
        term in text
        for term in (
            "sentiment", "mood", "bullish", "bearish", "feeling",
            "rally", "rallying", "inflow", "inflows", "crash", "selloff",
        )
    )
    has_coin = any(term in text for term in coin_terms)

    if not asks_sentiment and any(term in text for term in ("technology", "technical", "whitepaper", "explain")):
        return {
            "needs_sentiment": False,
            "needs_rag": True,
            "sentiment_scope": None,
            "sentiment_days": None,
            "date_range": None,
        }
    if not asks_sentiment and text.strip() in {"hello", "hi", "hey"}:
        return {
            "needs_sentiment": False,
            "needs_rag": False,
            "sentiment_scope": None,
            "sentiment_days": None,
            "date_range": None,
        }

    days = 7
    if any(term in text for term in ("last month", "past month", "30 days")):
        days = 30
    elif any(term in text for term in ("3 months", "quarter", "90 days")):
        days = 90

    return {
        "needs_sentiment": asks_sentiment or "market" in text,
        "needs_rag": any(term in text for term in ("news", "event", "why", "right now", "etf", "inflow", "inflows")),
        "sentiment_scope": "coin" if has_coin else "global",
        "sentiment_days": days,
        "date_range": None,
    }


def _lexical_sentiment(text: str) -> SentimentResult:
    terms = _tokens(text)
    bullish_hits = len(terms & BULLISH_TERMS)
    bearish_hits = len(terms & BEARISH_TERMS)

    if bullish_hits > bearish_hits:
        label = "Bullish"
        scores = {"bullish": 0.78, "bearish": 0.08, "neutral": 0.14}
    elif bearish_hits > bullish_hits:
        label = "Bearish"
        scores = {"bullish": 0.09, "bearish": 0.76, "neutral": 0.15}
    else:
        label = "Neutral"
        scores = {"bullish": 0.2, "bearish": 0.18, "neutral": 0.62}

    return SentimentResult(label=label, confidence=max(scores.values()), scores=scores)


def predict_sentiment(text: str) -> SentimentResult:
    if not text or not text.strip():
        raise ValueError("text cannot be empty")
    if not _mock_enabled():
        _real_mode_unavailable()
        content = _chat_completion(
            model=_sentiment_model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a crypto sentiment classifier. Return only JSON with "
                        'label, confidence, and scores keys. Label must be Bullish, Bearish, or Neutral.'
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=256,
        )
        return _sentiment_from_text(content)

    return _lexical_sentiment(text)


def classify_intent(prompt: str) -> dict[str, Any]:
    if not prompt or not prompt.strip():
        raise ValueError("prompt cannot be empty")
    if not _mock_enabled():
        _real_mode_unavailable()
        content = _chat_completion(
            model=_chat_model(),
            messages=[
                {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=128,
        )
        return _intent_from_text(content)

    return _mock_intent(prompt)


def batch_predict_sentiment(texts: list[str]) -> list[SentimentResult]:
    if not texts:
        raise ValueError("texts cannot be empty")
    if not _mock_enabled():
        return [predict_sentiment(text) for text in texts]
    return [predict_sentiment(text) for text in texts]


def generate_response(prompt: str, context: str = "", max_tokens: int = 512) -> GenerationResult:
    if not prompt or not prompt.strip():
        raise ValueError("prompt cannot be empty")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if not _mock_enabled():
        _real_mode_unavailable()
        user_content = prompt if not context.strip() else f"Context:\n{context.strip()}\n\nQuestion:\n{prompt.strip()}"
        text = _chat_completion(
            model=_chat_model(),
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional crypto research assistant. Answer concisely and factually.",
                },
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return GenerationResult(
            text=text.replace("<|eot_id|>", "").strip(),
            model_name=_chat_model(),
        )

    clean_prompt = prompt.strip().replace("<|eot_id|>", "")
    clean_context = context.strip().replace("<|eot_id|>", "")
    prefix = "Mock LoRA response"
    if clean_context:
        text = f"{prefix}: using the supplied context, {clean_prompt[:max_tokens]}"
    else:
        text = f"{prefix}: {clean_prompt[:max_tokens]}"
    return GenerationResult(text=text, model_name="mock-lora-fallback")
