import json
from collections import defaultdict
from datetime import date, timedelta, datetime
from pathlib import Path
from src.mock.mock_data import MOCK_SUMMARY_TEMPLATE

VALID_PERIODS = {"7d", "30d", "90d"}
PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "sentiment_summary.json"
_TREND_DATA: list[dict] = json.loads(_DATA_FILE.read_text())
_LAST_DATE = datetime.strptime(f"2026-{_TREND_DATA[-1]['date']}", "%Y-%m-%d").date() if _TREND_DATA else date.today()


def _period_range(period: str) -> tuple[str, str]:
    end = max(date.today(), _LAST_DATE)
    days = PERIOD_DAYS[period]
    return (end - timedelta(days=days - 1)).isoformat(), end.isoformat()


def _build_coin_timeline(coin: str, start: str, end: str) -> list[dict]:
    from src.services.sentiment_cache import sentiment_cache
    records = [
        r for r in sentiment_cache._coin_records.get(coin, [])
        if start <= r["date"] <= end
    ]
    by_date: dict[str, dict] = defaultdict(lambda: {"bullish": 0, "bearish": 0, "neutral": 0})
    for r in records:
        by_date[r["date"]][r["output"].lower()] += 1
    timeline = []
    for date_str in sorted(by_date):
        d = datetime.strptime(date_str, "%Y-%m-%d")
        c = by_date[date_str]
        timeline.append({"date": d.strftime("%m-%d"), "bullish": c["bullish"], "bearish": c["bearish"], "neutral": c["neutral"]})
    return timeline


def get_summary(crypto: str, period: str) -> dict:
    if period not in VALID_PERIODS:
        raise ValueError(f"Unsupported period '{period}'. Choose from {VALID_PERIODS}.")

    coin = crypto.upper()

    if coin == "ALL":
        days = PERIOD_DAYS[period]
        trend = _TREND_DATA[-days:]
    else:
        start, end = _period_range(period)
        trend = _build_coin_timeline(coin, start, end)

    total_bullish = sum(t["bullish"] for t in trend)
    total_bearish = sum(t["bearish"] for t in trend)
    total_neutral = sum(t["neutral"] for t in trend)
    overall = max(
        ("Bullish", total_bullish),
        ("Bearish", total_bearish),
        ("Neutral", total_neutral),
        key=lambda x: x[1],
    )[0]

    return {
        "crypto": coin,
        "period": period,
        "overall_sentiment": overall,
        "trend": trend,
        "top_topics": MOCK_SUMMARY_TEMPLATE[period]["top_topics"],
        "data_points_analyzed": total_bullish + total_bearish + total_neutral,
    }
