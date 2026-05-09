import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.types import Entity


def build_messages(
    user_message: str,
    rag_context: str,
    sentiment: dict | None,
    entities: list[Entity],
    history: list[dict],
    intent=None,
) -> list[dict]:
    system_parts = [
        "You are CryptoPulse, an AI assistant specializing in cryptocurrency market "
        "sentiment and risk intelligence. Provide concise, factual insights grounded "
        "in the data provided. Do not speculate beyond the provided data.",
    ]

    if rag_context:
        system_parts.append(f"\nRetrieved Knowledge:\n{rag_context}")

    if sentiment:
        period = sentiment.get("period", "7d")
        scope = getattr(intent, "sentiment_scope", None) if intent else None
        if scope == "global" or not [e for e in entities if e.type == "CRYPTO"]:
            label = f"Overall Market Sentiment (past {period})"
        else:
            names = ", ".join(e.text for e in entities if e.type == "CRYPTO")
            label = f"Market Sentiment for {names} (past {period})"
        system_parts.append(
            f"\n{label}: {sentiment['overall']} "
            f"(Bullish {sentiment['bullish']:.0%} / "
            f"Bearish {sentiment['bearish']:.0%} / "
            f"Neutral {sentiment['neutral']:.0%}, "
            f"based on {sentiment.get('sample_count', 'N/A')} social media posts)"
        )

    if entities:
        all_entities = ", ".join(f"{e.text} ({e.type})" for e in entities)
        system_parts.append(f"\nDetected entities: {all_entities}")

    return [
        {"role": "system", "content": "\n".join(system_parts)},
        *history,
        {"role": "user", "content": user_message},
    ]
