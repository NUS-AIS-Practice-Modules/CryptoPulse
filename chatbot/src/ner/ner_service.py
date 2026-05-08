import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.types import Entity
from src.config import settings

logger = logging.getLogger(__name__)


def extract_entities(text: str) -> list[Entity]:
    if settings.use_mock:
        return _mock_entities(text)

    backend = settings.ner_backend.lower()
    if backend == "lora":
        try:
            return _with_local_supplement(_extract_with_lora(text), text)
        except Exception as exc:
            logger.warning("LoRA NER failed; falling back to OpenAI NER: %s", exc)
        try:
            return _with_local_supplement(_extract_with_openai(text), text)
        except Exception as exc:
            logger.error("OpenAI NER fallback failed; using local rules: %s", exc)
            return _mock_entities(text)

    if backend == "llm":
        return _with_local_supplement(_extract_with_openai(text), text)

    # model backend (BERTweet — future)
    raise NotImplementedError("model NER backend not yet implemented")


def _configure_lora_environment() -> None:
    os.environ["LORA_USE_MOCK"] = "true" if settings.lora_use_mock else "false"
    if settings.lora_remote_base_url:
        os.environ["LORA_REMOTE_BASE_URL"] = settings.lora_remote_base_url
    if settings.lora_remote_api_key:
        os.environ["LORA_REMOTE_API_KEY"] = settings.lora_remote_api_key
    os.environ["LORA_REMOTE_TIMEOUT_SECONDS"] = str(settings.lora_remote_timeout_seconds)
    os.environ["LORA_SENTIMENT_MODEL"] = settings.lora_sentiment_model
    os.environ["LORA_CHAT_MODEL"] = settings.lora_chat_model


def _extract_with_lora(text: str) -> list[Entity]:
    _configure_lora_environment()
    from lora.src.inference import extract_entities as lora_extract_entities  # type: ignore
    from src.ner.llm_ner import entities_from_payload

    payload = lora_extract_entities(text)
    return entities_from_payload(payload, text)


def _extract_with_openai(text: str) -> list[Entity]:
    from src.ner.llm_ner import extract_entities as llm_extract

    return llm_extract(text)


def _dedupe_entities(entities: list[Entity]) -> list[Entity]:
    seen: set[tuple[str, str]] = set()
    deduped: list[Entity] = []
    for entity in entities:
        key = (entity.text.lower(), entity.type)
        if key in seen:
            continue
        deduped.append(entity)
        seen.add(key)
    return deduped


def _with_local_supplement(entities: list[Entity], text: str) -> list[Entity]:
    return _dedupe_entities([*entities, *_mock_entities(text)])


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
