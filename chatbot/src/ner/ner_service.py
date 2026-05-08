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
        "bitcoin": ("BTC", "CRYPTO"), "btc": ("BTC", "CRYPTO"),
        "ethereum": ("ETH", "CRYPTO"), "eth": ("ETH", "CRYPTO"),
        "solana": ("SOL", "CRYPTO"), "sol": ("SOL", "CRYPTO"),
        "binance coin": ("BNB", "CRYPTO"), "bnb": ("BNB", "CRYPTO"),
        "ripple": ("XRP", "CRYPTO"), "xrp": ("XRP", "CRYPTO"),
        "dogecoin": ("DOGE", "CRYPTO"), "doge": ("DOGE", "CRYPTO"),
        "binance": ("Binance", "EXCHANGE"),
        "coinbase": ("Coinbase", "EXCHANGE"),
        "kraken": ("Kraken", "EXCHANGE"),
        "sec": ("SEC", "REGULATORY_BODY"),
        "cftc": ("CFTC", "REGULATORY_BODY"),
        "ftx": ("FTX Collapse", "EVENT"),
        "etf approval": ("ETF Approval", "EVENT"),
    }
    lower = text.lower()
    seen: set[str] = set()
    results: list[Entity] = []
    for mention, (normalized, entity_type) in known.items():
        if normalized in seen:
            continue
        idx = lower.find(mention)
        if idx != -1:
            results.append(Entity(
                text=normalized,
                type=entity_type,
                start=idx,
                end=idx + len(mention),
                confidence=0.99,
            ))
            seen.add(normalized)
    return results
