from datetime import date, timedelta

MOCK_RAG_CONTEXT = """
Bitcoin (BTC) is the first and most widely adopted cryptocurrency, created by Satoshi Nakamoto in 2009.
It operates on a decentralized blockchain using Proof-of-Work consensus. The Bitcoin Halving event occurs
approximately every four years, reducing the block reward by 50% and historically preceding bull markets.
Ethereum (ETH) is a programmable blockchain platform enabling smart contracts and decentralized applications.
Market sentiment in crypto is heavily influenced by regulatory developments (SEC rulings, MiCA in EU),
macroeconomic factors (interest rates, inflation), and large institutional flows.
"""

MOCK_SOURCES = [
    {
        "title": "Bitcoin Whitepaper",
        "relevance": 0.92,
        "snippet": "A purely peer-to-peer version of electronic cash...",
    },
    {
        "title": "CoinGecko Market Overview",
        "relevance": 0.85,
        "snippet": "BTC dominance and market cap trends...",
    },
]

MOCK_ENTITIES = [
    {"text": "BTC", "type": "CRYPTO", "start": 0, "end": 3, "confidence": 0.95}
]

MOCK_SENTIMENT = {
    "label": "Bullish",
    "confidence": 0.82,
    "breakdown": {"bullish": 0.82, "bearish": 0.10, "neutral": 0.08},
}

MOCK_REPLY = (
    "Based on current market analysis, Bitcoin (BTC) sentiment is predominantly bullish. "
    "Recent on-chain metrics and social media activity suggest strong accumulation by long-term holders. "
    "However, please note this is a mock response — real insights require live data."
)


def _make_trend(days: int) -> list[dict]:
    today = date.today()
    import random
    random.seed(42)
    trend = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        b = round(0.55 + random.uniform(-0.1, 0.15), 2)
        be = round(random.uniform(0.10, 0.25), 2)
        n = round(max(0.0, 1 - b - be), 2)
        trend.append({"date": d.isoformat(), "bullish": b, "bearish": be, "neutral": n})
    return trend


MOCK_SUMMARY_TEMPLATE = {
    "7d": {
        "overall_sentiment": "Bullish",
        "top_topics": ["ETF approval", "Halving", "Institutional adoption"],
        "data_points_analyzed": 15234,
    },
    "30d": {
        "overall_sentiment": "Neutral",
        "top_topics": ["SEC ruling", "Layer-2 growth", "DeFi TVL"],
        "data_points_analyzed": 62840,
    },
    "90d": {
        "overall_sentiment": "Bullish",
        "top_topics": ["Halving cycle", "ETF inflows", "Macro rate cuts"],
        "data_points_analyzed": 187000,
    },
}
