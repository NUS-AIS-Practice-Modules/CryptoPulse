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
