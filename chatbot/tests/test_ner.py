import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["USE_MOCK"] = "true"

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
