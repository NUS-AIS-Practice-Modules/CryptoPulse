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


def _fallback_entities(text: str) -> list[Entity]:
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
    entities: list[Entity] = []
    for mention, ticker in known.items():
        if ticker in seen:
            continue
        start = lower.find(mention)
        if start == -1:
            continue
        entities.append(Entity(
            text=ticker,
            type="CRYPTO",
            start=start,
            end=start + len(mention),
            confidence=0.75,
        ))
        seen.add(ticker)
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
        entities = []
        for item in data.get("entities", []):
            normalized = item.get("normalized", "")
            original = item.get("original_mention", normalized)
            start, end = _find_offset(text, original)
            entities.append(Entity(
                text=normalized,
                type=item.get("type", "CRYPTO"),
                start=start,
                end=end,
                confidence=float(item.get("confidence", 0.9)),
            ))
        return entities
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("NER JSON parse failed: %s | raw=%s", e, raw[:200])
        return _fallback_entities(text)
