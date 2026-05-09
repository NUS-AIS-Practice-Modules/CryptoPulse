import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services import intent_service


def test_classify_intent_uses_lora_backend(monkeypatch):
    monkeypatch.setattr(intent_service.settings, "llm_backend", "lora")

    calls = {}

    def fake_lora(message):
        calls["message"] = message
        return {
            "needs_sentiment": True,
            "needs_rag": False,
            "sentiment_scope": "coin",
            "sentiment_days": 7,
            "date_range": None,
        }

    monkeypatch.setattr(intent_service, "_classify_with_lora", fake_lora)

    intent = intent_service.classify_intent("What is BTC sentiment this week?", "unused", "unused")

    assert calls["message"] == "What is BTC sentiment this week?"
    assert intent.needs_sentiment is True
    assert intent.needs_rag is False
    assert intent.sentiment_scope == "coin"
    assert intent.date_range is not None


def test_classify_intent_keeps_openai_backend(monkeypatch):
    monkeypatch.setattr(intent_service.settings, "llm_backend", "openai")

    calls = {}

    def fake_openai(message, api_key, model):
        calls["args"] = (message, api_key, model)
        return {
            "needs_sentiment": False,
            "needs_rag": True,
            "sentiment_scope": None,
            "sentiment_days": None,
            "date_range": None,
        }

    monkeypatch.setattr(intent_service, "_classify_with_openai", fake_openai)

    intent = intent_service.classify_intent("Tell me about Ethereum technology", "key", "model")

    assert calls["args"] == ("Tell me about Ethereum technology", "key", "model")
    assert intent.needs_sentiment is False
    assert intent.needs_rag is True
    assert intent.sentiment_scope is None
    assert intent.date_range is None


def test_classify_intent_falls_back_when_backend_fails(monkeypatch):
    monkeypatch.setattr(intent_service.settings, "llm_backend", "lora")

    def broken_lora(message):
        raise RuntimeError("boom")

    monkeypatch.setattr(intent_service, "_classify_with_lora", broken_lora)

    intent = intent_service.classify_intent("anything", "unused", "unused")

    assert intent.needs_sentiment is True
    assert intent.needs_rag is True
    assert intent.sentiment_scope == "global"
    assert intent.date_range is not None


def test_intent_payload_parses_string_booleans():
    intent = intent_service._intent_from_payload({
        "needs_sentiment": "false",
        "needs_rag": "false",
        "sentiment_scope": "coin",
        "sentiment_days": None,
        "date_range": None,
    })

    assert intent.needs_sentiment is False
    assert intent.needs_rag is False
    assert intent.sentiment_scope == "coin"


def test_policy_overrides_failed_real_intent_matrix_cases(monkeypatch):
    monkeypatch.setattr(intent_service.settings, "llm_backend", "lora")

    bad_lora_outputs = {
        "What is a blockchain?": {
            "needs_sentiment": False,
            "needs_rag": True,
            "sentiment_scope": None,
            "sentiment_days": None,
            "date_range": None,
        },
        "Tell me about the FTX collapse.": {
            "needs_sentiment": True,
            "needs_rag": True,
            "sentiment_scope": "global",
            "sentiment_days": None,
            "date_range": None,
        },
        "What did the SEC and CFTC do regarding Bitcoin ETF approval?": {
            "needs_sentiment": True,
            "needs_rag": False,
            "sentiment_scope": "global",
            "sentiment_days": None,
            "date_range": None,
        },
        "Compare Binance, Coinbase and Kraken as crypto exchanges.": {
            "needs_sentiment": True,
            "needs_rag": True,
            "sentiment_scope": "global",
            "sentiment_days": None,
            "date_range": None,
        },
        "Is Bitcoin bullish right now and what has been happening with it recently?": {
            "needs_sentiment": True,
            "needs_rag": False,
            "sentiment_scope": "coin",
            "sentiment_days": None,
            "date_range": None,
        },
    }

    monkeypatch.setattr(intent_service, "_classify_with_lora", lambda message: bad_lora_outputs[message])

    expectations = {
        "What is a blockchain?": (False, False),
        "Tell me about the FTX collapse.": (False, True),
        "What did the SEC and CFTC do regarding Bitcoin ETF approval?": (False, True),
        "Compare Binance, Coinbase and Kraken as crypto exchanges.": (False, True),
        "Is Bitcoin bullish right now and what has been happening with it recently?": (True, True),
    }

    for message, expected in expectations.items():
        intent = intent_service.classify_intent(message, "unused", "unused")
        assert (intent.needs_sentiment, intent.needs_rag) == expected
