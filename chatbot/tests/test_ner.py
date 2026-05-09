import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["USE_MOCK"] = "true"

import src.ner.ner_service as ner_service
from src.ner.ner_service import extract_entities
from src.ner.llm_ner import _fallback_entities, _normalize_entity_text


def test_bitcoin_detected():
    entities = extract_entities("Bitcoin is going to the moon!")
    tickers = [e.text for e in entities]
    assert "BTC" in tickers


def test_ethereum_detected():
    entities = extract_entities("I love ethereum and eth staking")
    tickers = [e.text for e in entities]
    assert "ETH" in tickers


def test_no_entities_for_generic_text():
    entities = extract_entities("The weather is nice today.")
    assert entities == []


def test_entity_type_is_crypto():
    entities = extract_entities("BTC is mooning!")
    assert all(e.type == "CRYPTO" for e in entities)


def test_entity_confidence_in_range():
    entities = extract_entities("Bitcoin price is rising")
    for e in entities:
        assert 0.0 <= e.confidence <= 1.0


def test_empty_string_returns_empty():
    assert extract_entities("") == []


def test_fallback_detects_regulators_and_exchanges():
    entities = _fallback_entities("Compare Binance, Coinbase and Kraken after SEC and CFTC action on FTX.")
    by_text = {e.text: e.type for e in entities}

    assert by_text["Binance"] == "EXCHANGE"
    assert by_text["Coinbase"] == "EXCHANGE"
    assert by_text["Kraken"] == "EXCHANGE"
    assert by_text["SEC"] == "REGULATORY_BODY"
    assert by_text["CFTC"] == "REGULATORY_BODY"
    assert by_text["FTX Collapse"] == "EVENT"


def test_exchange_entities_are_normalized_from_llm_aliases():
    assert _normalize_entity_text("BNB", "Binance", "EXCHANGE") == "Binance"
    assert _normalize_entity_text("COIN", "Coinbase", "EXCHANGE") == "Coinbase"
    assert _normalize_entity_text("KRK", "Kraken", "EXCHANGE") == "Kraken"
    assert _normalize_entity_text("FTX", "FTX", "EVENT") == "FTX Collapse"


def test_lora_backend_uses_lora_ner_first(monkeypatch):
    monkeypatch.setattr(ner_service.settings, "use_mock", False)
    monkeypatch.setattr(ner_service.settings, "ner_backend", "lora")

    def fake_lora(text):
        assert text == "Bitcoin and SEC"
        return [ner_service.Entity(text="BTC", type="CRYPTO", start=0, end=7, confidence=0.95)]

    monkeypatch.setattr(ner_service, "_extract_with_lora", fake_lora)
    entities = ner_service.extract_entities("Bitcoin and SEC")

    assert [entity.text for entity in entities] == ["BTC", "SEC"]


def test_lora_backend_falls_back_to_openai(monkeypatch):
    monkeypatch.setattr(ner_service.settings, "use_mock", False)
    monkeypatch.setattr(ner_service.settings, "ner_backend", "lora")

    def fail_lora(_text):
        raise RuntimeError("lora unavailable")

    def fake_openai(text):
        assert text == "Ethereum"
        return [ner_service.Entity(text="ETH", type="CRYPTO", start=0, end=8, confidence=0.9)]

    monkeypatch.setattr(ner_service, "_extract_with_lora", fail_lora)
    monkeypatch.setattr(ner_service, "_extract_with_openai", fake_openai)

    entities = ner_service.extract_entities("Ethereum")
    assert [entity.text for entity in entities] == ["ETH"]


def test_lora_backend_falls_back_to_local_rules(monkeypatch):
    monkeypatch.setattr(ner_service.settings, "use_mock", False)
    monkeypatch.setattr(ner_service.settings, "ner_backend", "lora")

    def fail(_text):
        raise RuntimeError("backend failed")

    monkeypatch.setattr(ner_service, "_extract_with_lora", fail)
    monkeypatch.setattr(ner_service, "_extract_with_openai", fail)

    entities = ner_service.extract_entities("Compare Binance, Coinbase and Kraken.")
    by_text = {entity.text: entity.type for entity in entities}

    assert by_text["Binance"] == "EXCHANGE"
    assert by_text["Coinbase"] == "EXCHANGE"
    assert by_text["Kraken"] == "EXCHANGE"


def test_lora_backend_supplements_empty_result_with_local_rules(monkeypatch):
    monkeypatch.setattr(ner_service.settings, "use_mock", False)
    monkeypatch.setattr(ner_service.settings, "ner_backend", "lora")

    monkeypatch.setattr(ner_service, "_extract_with_lora", lambda _text: [])

    entities = ner_service.extract_entities("What did the SEC and CFTC do regarding Bitcoin ETF approval?")
    by_text = {entity.text: entity.type for entity in entities}

    assert by_text["SEC"] == "REGULATORY_BODY"
    assert by_text["CFTC"] == "REGULATORY_BODY"
    assert by_text["BTC"] == "CRYPTO"
    assert by_text["ETF Approval"] == "EVENT"
