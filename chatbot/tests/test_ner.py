import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["USE_MOCK"] = "true"

from src.ner.ner_service import extract_entities


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
