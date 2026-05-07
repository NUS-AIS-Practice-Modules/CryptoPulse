import logging
from datetime import datetime, timezone

from src.config import settings
from src.ner.ner_service import extract_entities
from src.services.sentiment_cache import sentiment_cache
from src.services.intent_service import classify_intent, Intent
from src.memory.conversation_store import conversation_store
from src.prompts.chat_prompt import build_messages

logger = logging.getLogger(__name__)


def _configure_lora_environment() -> None:
    import os

    os.environ["LORA_USE_MOCK"] = "true" if settings.lora_use_mock else "false"
    if settings.lora_remote_base_url:
        os.environ["LORA_REMOTE_BASE_URL"] = settings.lora_remote_base_url
    if settings.lora_remote_api_key:
        os.environ["LORA_REMOTE_API_KEY"] = settings.lora_remote_api_key
    os.environ["LORA_REMOTE_TIMEOUT_SECONDS"] = str(settings.lora_remote_timeout_seconds)
    os.environ["LORA_SENTIMENT_MODEL"] = settings.lora_sentiment_model
    os.environ["LORA_CHAT_MODEL"] = settings.lora_chat_model


def _get_rag_context(query: str) -> tuple[str, list[dict]]:
    if settings.use_mock or settings.rag_use_mock:
        from src.mock.mock_rag import get_context_for_llm, retrieve
        context = get_context_for_llm(query)
        result = retrieve(query)
        return context, result["documents"]

    from rag.src.retrieval import get_context_for_llm, retrieve  # type: ignore
    context = get_context_for_llm(query)
    result = retrieve(query)
    return context, [
        {"title": d.title, "relevance": d.relevance_score, "snippet": d.content[:120]}
        for d in result.documents
    ]


def _generate_reply(messages: list[dict]) -> str:
    if settings.use_mock:
        from src.mock.mock_data import MOCK_REPLY
        return MOCK_REPLY

    if settings.llm_backend == "lora":
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        _configure_lora_environment()
        from lora.src.inference import generate_response  # type: ignore
        # Flatten messages into a single prompt string for LoRA interface
        prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        result = generate_response(prompt)
        return result.text

    # Default: OpenAI
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    return response.choices[0].message.content or ""


async def handle_chat(
    message: str,
    conversation_id: str,
    include_sentiment: bool = True,
    include_sources: bool = True,
) -> dict:
    # Step 1: Intent classification
    if settings.use_mock:
        from datetime import date, timedelta
        today = date.today()
        intent = Intent(needs_sentiment=True, needs_rag=True, sentiment_scope="global",
                        date_range={"start": (today - timedelta(days=6)).isoformat(), "end": today.isoformat()})
    else:
        intent = classify_intent(message, settings.openai_api_key, settings.openai_ner_model)
    logger.info("Intent: %s", intent)

    # Step 2: NER
    entities = extract_entities(message)
    crypto_entities = [e for e in entities if e.type == "CRYPTO"]
    logger.info("NER: %s", [(e.text, e.type) for e in entities])

    # Step 3: Sentiment lookup (only when needed)
    sentiment: dict | None = None
    if include_sentiment and intent.needs_sentiment:
        if not settings.use_mock and settings.llm_backend == "lora":
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            _configure_lora_environment()
            from lora.src.inference import predict_sentiment  # type: ignore
            result = predict_sentiment(message)
            sentiment = {
                "overall": result.label,
                "confidence": result.confidence,
                "bullish": result.scores.get("bullish", 0.0),
                "bearish": result.scores.get("bearish", 0.0),
                "neutral": result.scores.get("neutral", 0.0),
            }
        elif intent.sentiment_scope == "coin" and crypto_entities:
            dr = intent.date_range or {}
            sentiment = sentiment_cache.lookup_coin_date_range(
                crypto_entities[0].text,
                dr.get("start", "2026-05-01"),
                dr.get("end", "2026-05-07"),
            )
        else:
            dr = intent.date_range or {}
            sentiment = sentiment_cache.lookup_date_range(
                dr.get("start", "2026-05-01"), dr.get("end", "2026-05-07")
            )

    # Step 4: RAG retrieval (only when needed)
    rag_context, sources = "", []
    if intent.needs_rag:
        entity_texts = [e.text for e in entities]
        rag_query = f"{message} {' '.join(entity_texts)}" if entity_texts else message
        rag_context, sources = _get_rag_context(rag_query)

    # Step 5: Load conversation history
    history = conversation_store.get_recent_messages(conversation_id, settings.max_history_turns)

    # Step 6: Build prompt and generate reply
    messages_list = build_messages(message, rag_context, sentiment, entities, history, intent)
    reply = _generate_reply(messages_list)

    # Step 6: Persist turn
    conversation_store.append_turn(conversation_id, message, reply)

    # Step 7: Format response
    sentiment_payload = None
    if sentiment and include_sentiment:
        sentiment_payload = {
            "label": sentiment["overall"],
            "confidence": sentiment.get("confidence", sentiment.get("bullish", 0.5)),
            "breakdown": {
                "bullish": sentiment.get("bullish", 0.0),
                "bearish": sentiment.get("bearish", 0.0),
                "neutral": sentiment.get("neutral", 0.0),
            },
        }

    entities_payload = [
        {"text": e.text, "type": e.type, "start": e.start, "end": e.end, "confidence": e.confidence}
        for e in entities
    ]

    sources_payload = sources if include_sources else []

    return {
        "reply": reply,
        "sentiment": sentiment_payload,
        "entities": entities_payload,
        "sources": sources_payload,
        "conversation_id": conversation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
