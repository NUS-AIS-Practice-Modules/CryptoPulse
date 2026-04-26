import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.types import Entity
from src.config import settings


def extract_entities(text: str) -> list[Entity]:
    if settings.use_mock:
        return _mock_entities(text)

    if settings.ner_backend == "llm":
        from src.ner.llm_ner import extract_entities as llm_extract
        return llm_extract(text)

    # model backend (BERTweet — future)
    raise NotImplementedError("model NER backend not yet implemented")


def _mock_entities(text: str) -> list[Entity]:
    """Simple keyword-based mock for USE_MOCK=true."""
    known = {
        "bitcoin": "BTC", "btc": "BTC",
        "ethereum": "ETH", "eth": "ETH",
        "solana": "SOL", "sol": "SOL",
        "binance coin": "BNB", "bnb": "BNB",
        "ripple": "XRP", "xrp": "XRP",
        "dogecoin": "DOGE", "doge": "DOGE",
    }
    lower = text.lower()
    seen: set[str] = set()
    results: list[Entity] = []
    for mention, ticker in known.items():
        if ticker in seen:
            continue
        idx = lower.find(mention)
        if idx != -1:
            results.append(Entity(
                text=ticker,
                type="CRYPTO",
                start=idx,
                end=idx + len(mention),
                confidence=0.99,
            ))
            seen.add(ticker)
    return results
