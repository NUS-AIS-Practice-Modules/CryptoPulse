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
) -> list[dict]:
    system_parts = [
        "You are CryptoPulse, an AI assistant specializing in cryptocurrency market "
        "sentiment and risk intelligence. Provide concise, factual insights grounded "
        "in the retrieved context below. Do not speculate beyond the provided data.",
        f"\nRetrieved Knowledge:\n{rag_context}",
    ]

    crypto_entities = [e for e in entities if e.type == "CRYPTO"]
    if sentiment and crypto_entities:
        names = ", ".join(e.text for e in crypto_entities)
        system_parts.append(
            f"\nMarket Sentiment for {names}: {sentiment['overall']} "
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
