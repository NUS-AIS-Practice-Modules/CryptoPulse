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
    "moon",
    "rally",
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


def predict_sentiment(text: str) -> SentimentResult:
    if not text or not text.strip():
        raise ValueError("text cannot be empty")
    if not _mock_enabled():
        _real_mode_unavailable()
        response = _post_remote("/predict_sentiment", {"text": text})
        scores = response.get("scores") or response.get("breakdown") or {}
        return SentimentResult(
            label=str(response["label"]),
            confidence=float(response["confidence"]),
            scores={str(k): float(v) for k, v in scores.items()},
        )

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


def batch_predict_sentiment(texts: list[str]) -> list[SentimentResult]:
    if not texts:
        raise ValueError("texts cannot be empty")
    if not _mock_enabled():
        _real_mode_unavailable()
        response = _post_remote("/batch_predict_sentiment", {"texts": texts})
        items = response.get("results", response if isinstance(response, list) else [])
        return [
            SentimentResult(
                label=str(item["label"]),
                confidence=float(item["confidence"]),
                scores={str(k): float(v) for k, v in (item.get("scores") or item.get("breakdown") or {}).items()},
            )
            for item in items
        ]
    return [predict_sentiment(text) for text in texts]


def generate_response(prompt: str, context: str = "", max_tokens: int = 512) -> GenerationResult:
    if not prompt or not prompt.strip():
        raise ValueError("prompt cannot be empty")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if not _mock_enabled():
        _real_mode_unavailable()
        response = _post_remote(
            "/generate_response",
            {"prompt": prompt, "context": context, "max_tokens": max_tokens},
        )
        return GenerationResult(
            text=str(response["text"]).replace("<|eot_id|>", ""),
            model_name=str(response.get("model_name", "autodl-lora")),
        )

    clean_prompt = prompt.strip().replace("<|eot_id|>", "")
    clean_context = context.strip().replace("<|eot_id|>", "")
    prefix = "Mock LoRA response"
    if clean_context:
        text = f"{prefix}: using the supplied context, {clean_prompt[:max_tokens]}"
    else:
        text = f"{prefix}: {clean_prompt[:max_tokens]}"
    return GenerationResult(text=text, model_name="mock-lora-fallback")
