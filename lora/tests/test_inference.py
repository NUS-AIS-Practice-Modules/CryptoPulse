import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference import api
from src.inference import batch_predict_sentiment, classify_intent, generate_response, predict_sentiment


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
    monkeypatch.setenv("LORA_REMOTE_BASE_URL", "https://autodl.example/v1")

    def fake_post(path, payload):
        assert path == "/chat/completions"
        assert payload["model"] == "sentiment-lora"
        assert payload["temperature"] == 0.1
        assert payload["messages"][-1] == {"role": "user", "content": "Bitcoin rally"}
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"label":"bullish","confidence":0.91,"scores":{"bullish":0.91,"bearish":0.03}}'
                    }
                }
            ]
        }

    monkeypatch.setattr(api, "_post_remote", fake_post)
    result = api.predict_sentiment("Bitcoin rally")
    assert result.label == "Bullish"
    assert result.confidence == 0.91
    assert result.scores["neutral"] == 0.0


def test_real_mode_uses_remote_generation_endpoint(monkeypatch):
    monkeypatch.setenv("LORA_USE_MOCK", "false")
    monkeypatch.setenv("LORA_REMOTE_BASE_URL", "https://autodl.example/v1")

    def fake_post(path, payload):
        assert path == "/chat/completions"
        assert payload["model"] == "ift-lora"
        assert payload["temperature"] == 0.7
        assert payload["messages"][-1]["content"] == "Context:\nETF flows\n\nQuestion:\nExplain BTC"
        return {"choices": [{"message": {"content": "BTC looks constructive<|eot_id|>"}}]}

    monkeypatch.setattr(api, "_post_remote", fake_post)
    result = api.generate_response("Explain BTC", context="ETF flows")
    assert result.text == "BTC looks constructive"
    assert result.model_name == "ift-lora"


def test_classify_intent_mock_returns_json_shape():
    result = classify_intent("What is BTC sentiment this week?")

    assert result["needs_sentiment"] is True
    assert result["needs_rag"] is False
    assert result["sentiment_scope"] == "coin"
    assert result["sentiment_days"] == 7
    assert result["date_range"] is None


def test_real_mode_uses_remote_ift_for_intent(monkeypatch):
    monkeypatch.setenv("LORA_USE_MOCK", "false")
    monkeypatch.setenv("LORA_REMOTE_BASE_URL", "https://autodl.example/v1")

    def fake_post(path, payload):
        assert path == "/chat/completions"
        assert payload["model"] == "ift-lora"
        assert payload["temperature"] == 0
        assert payload["max_tokens"] == 128
        assert payload["messages"][-1] == {"role": "user", "content": "Hello"}
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"needs_sentiment":false,"needs_rag":false,"sentiment_scope":null,"sentiment_days":null,"date_range":null}'
                    }
                }
            ]
        }

    monkeypatch.setattr(api, "_post_remote", fake_post)
    result = api.classify_intent("Hello")
    assert result["needs_sentiment"] is False
    assert result["needs_rag"] is False


def test_intent_parser_handles_fenced_json_and_falls_back():
    parsed = api._intent_from_text(
        '```json\n{"needs_sentiment":true,"needs_rag":false,"sentiment_scope":"global","sentiment_days":30,"date_range":null}\n```'
    )
    assert parsed["sentiment_days"] == 30

    first_json = api._intent_from_text(
        '{"needs_sentiment":false,"needs_rag":true,"sentiment_scope":null,"sentiment_days":null,"date_range":null}\nUser: Hello'
    )
    assert first_json["needs_sentiment"] is False
    assert first_json["needs_rag"] is True

    key_value = api._intent_from_text(
        'needs_sentiment: false\nneeds_rag: false\nsentiment_scope: null\nsentiment_days: null\ndate_range: null'
    )
    assert key_value["needs_sentiment"] is False
    assert key_value["needs_rag"] is False
    assert key_value["sentiment_scope"] is None

    string_booleans = api._intent_from_text(
        '{"needs_sentiment":"false","needs_rag":"false","sentiment_scope":"COIN","sentiment_days":"7","date_range":null}'
    )
    assert string_booleans["needs_sentiment"] is False
    assert string_booleans["needs_rag"] is False
    assert string_booleans["sentiment_scope"] == "coin"

    fallback = api._intent_from_text("not json")
    assert fallback["needs_sentiment"] is True
    assert fallback["needs_rag"] is True
    assert fallback["sentiment_scope"] == "global"


def test_sentiment_fallback_parses_non_json_text():
    result = api._sentiment_from_text("This looks bearish after a sharp crash")
    assert result.label == "Bearish"
    assert set(result.scores) == {"bullish", "bearish", "neutral"}
