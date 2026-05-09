import json
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.types import Entity
from src.config import settings

logger = logging.getLogger(__name__)

_NER_PROMPT = """Extract cryptocurrency-related named entities from the text below.

Rules:
- CRYPTO: Always normalize to the official ticker symbol.
  Examples: "Bitcoin"→"BTC", "Ethereum"→"ETH", "Solana"→"SOL",
            "Binance Coin"→"BNB", "Ripple"→"XRP", "Cardano"→"ADA",
            "Dogecoin"→"DOGE", "Avalanche"→"AVAX", "Polygon"→"MATIC",
            "Litecoin"→"LTC", "Chainlink"→"LINK", "Polkadot"→"DOT"
- EXCHANGE: Use canonical exchange name. e.g., "Binance", "Coinbase", "Kraken", "OKX"
- PERSON: Full name as written. e.g., "Vitalik Buterin", "Elon Musk", "Satoshi Nakamoto"
- REGULATORY_BODY: Official abbreviation or name. e.g., "SEC", "CFTC", "EU MiCA", "Fed"
- EVENT: Short descriptive label. e.g., "Bitcoin Halving", "FTX Collapse", "ETF Approval"

Return ONLY valid JSON (no markdown, no explanation):
{{
  "entities": [
    {{
      "normalized": "BTC",
      "original_mention": "Bitcoin",
      "type": "CRYPTO",
      "confidence": 0.95
    }}
  ]
}}
If no entities found, return: {{"entities": []}}

Text: {text}"""


def _find_offset(text: str, mention: str) -> tuple[int, int]:
    idx = text.lower().find(mention.lower())
    if idx == -1:
        return 0, 0
    return idx, idx + len(mention)


def _normalize_entity_text(normalized: str, original: str, entity_type: str) -> str:
    if entity_type == "EXCHANGE":
        original_key = original.strip().lower()
        normalized_key = normalized.strip().lower()
        exchanges = {
            "binance": "Binance",
            "bnb": "Binance",
            "coinbase": "Coinbase",
            "coin": "Coinbase",
            "kraken": "Kraken",
            "krk": "Kraken",
            "okx": "OKX",
        }
        return exchanges.get(original_key) or exchanges.get(normalized_key) or normalized
    if entity_type == "EVENT":
        original_key = original.strip().lower()
        normalized_key = normalized.strip().lower()
        events = {
            "ftx": "FTX Collapse",
            "ftx collapse": "FTX Collapse",
            "etf": "ETF Approval",
            "bitcoin etf": "ETF Approval",
            "etf approval": "ETF Approval",
        }
        return events.get(original_key) or events.get(normalized_key) or normalized
    return normalized


def entities_from_payload(data: dict, text: str) -> list[Entity]:
    entities: list[Entity] = []
    seen: set[tuple[str, str]] = set()
    for item in data.get("entities", []):
        normalized = str(item.get("normalized", "")).strip()
        original = str(item.get("original_mention", normalized)).strip()
        entity_type = str(item.get("type", "CRYPTO")).strip().upper()
        if not normalized:
            continue
        normalized_text = _normalize_entity_text(normalized, original, entity_type)
        key = (normalized_text.lower(), entity_type)
        if key in seen:
            continue
        start, end = _find_offset(text, original)
        try:
            confidence = float(item.get("confidence", 0.9))
        except (TypeError, ValueError):
            confidence = 0.9
        entities.append(Entity(
            text=normalized_text,
            type=entity_type,
            start=start,
            end=end,
            confidence=max(0.0, min(1.0, confidence)),
        ))
        seen.add(key)
    return entities


def _fallback_entities(text: str) -> list[Entity]:
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
    entities: list[Entity] = []
    for mention, (normalized, entity_type) in known.items():
        if normalized in seen:
            continue
        start = lower.find(mention)
        if start == -1:
            continue
        entities.append(Entity(
            text=normalized,
            type=entity_type,
            start=start,
            end=start + len(mention),
            confidence=0.75,
        ))
        seen.add(normalized)
    return entities


def extract_entities(text: str) -> list[Entity]:
    if not text.strip():
        return []

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_ner_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": _NER_PROMPT.format(text=text)}
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content or "{}"
    except Exception as e:
        logger.error("OpenAI NER call failed: %s", e)
        return _fallback_entities(text)

    try:
        data = json.loads(raw)
        return entities_from_payload(data, text)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("NER JSON parse failed: %s | raw=%s", e, raw[:200])
        return _fallback_entities(text)
