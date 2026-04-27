import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference import api
from src.inference import batch_predict_sentiment, generate_response, predict_sentiment


def test_predict_sentiment_returns_shared_shape():
    result = predict_sentiment("Bitcoin ETF approval could trigger a strong rally")
    assert result.label == "Bullish"
    assert result.confidence > 0
    assert set(result.scores) == {"bullish", "bearish", "neutral"}


def test_batch_predict_sentiment_rejects_empty_batch():
    with pytest.raises(ValueError):
        batch_predict_sentiment([])


def test_generate_response_strips_special_tokens():
    result = generate_response("Explain BTC<|eot_id|>", context="ETF flows<|eot_id|>")
    assert "<|eot_id|>" not in result.text
    assert result.model_name == "mock-lora-fallback"


def test_real_mode_without_model_path_raises(monkeypatch):
    monkeypatch.setenv("LORA_USE_MOCK", "false")
    monkeypatch.delenv("LORA_REMOTE_BASE_URL", raising=False)
    monkeypatch.delenv("LORA_MODEL_PATH", raising=False)
    with pytest.raises(RuntimeError, match="LORA_REMOTE_BASE_URL"):
        predict_sentiment("Bitcoin is neutral")
    monkeypatch.setenv("LORA_USE_MOCK", os.getenv("LORA_USE_MOCK", "true"))


def test_real_mode_uses_remote_sentiment_endpoint(monkeypatch):
    monkeypatch.setenv("LORA_USE_MOCK", "false")
    monkeypatch.setenv("LORA_REMOTE_BASE_URL", "https://autodl.example")

    def fake_post(path, payload):
        assert path == "/predict_sentiment"
        assert payload == {"text": "Bitcoin rally"}
        return {
            "label": "Bullish",
            "confidence": 0.91,
            "scores": {"bullish": 0.91, "bearish": 0.03, "neutral": 0.06},
        }

    monkeypatch.setattr(api, "_post_remote", fake_post)
    result = api.predict_sentiment("Bitcoin rally")
    assert result.label == "Bullish"
    assert result.confidence == 0.91


def test_real_mode_uses_remote_generation_endpoint(monkeypatch):
    monkeypatch.setenv("LORA_USE_MOCK", "false")
    monkeypatch.setenv("LORA_REMOTE_BASE_URL", "https://autodl.example")

    def fake_post(path, payload):
        assert path == "/generate_response"
        assert payload["prompt"] == "Explain BTC"
        assert payload["context"] == "ETF flows"
        return {"text": "BTC looks constructive<|eot_id|>", "model_name": "autodl-lora"}

    monkeypatch.setattr(api, "_post_remote", fake_post)
    result = api.generate_response("Explain BTC", context="ETF flows")
    assert result.text == "BTC looks constructive"
    assert result.model_name == "autodl-lora"
