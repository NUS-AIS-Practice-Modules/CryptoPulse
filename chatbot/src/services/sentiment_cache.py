import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}
_DATA_YEAR = 2026


def _to_full_date(mm_dd: str) -> str:
    return f"{_DATA_YEAR}-{mm_dd}"


def _aggregate(entries: list[dict], label: str) -> dict | None:
    if not entries:
        return None
    bullish = sum(t["bullish"] for t in entries)
    bearish = sum(t["bearish"] for t in entries)
    neutral = sum(t["neutral"] for t in entries)
    total = bullish + bearish + neutral or 1
    overall = max(("Bullish", bullish), ("Bearish", bearish), ("Neutral", neutral), key=lambda x: x[1])[0]
    return {
        "overall": overall,
        "bullish": bullish / total,
        "bearish": bearish / total,
        "neutral": neutral / total,
        "sample_count": total,
        "period": label,
    }


class SentimentCache:
    def __init__(self) -> None:
        self._timeline: list[dict] = []

    def load(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            logger.warning("sentiment_summary.json not found at %s — sentiment lookup disabled", path)
            return
        self._timeline = json.loads(p.read_text(encoding="utf-8"))
        logger.info("Loaded sentiment cache: %d days of timeline data", len(self._timeline))

    def lookup_period(self, period: str) -> dict | None:
        days = _PERIOD_DAYS.get(period, 7)
        recent = self._timeline[-days:] if len(self._timeline) >= days else self._timeline
        return _aggregate(recent, period)

    def lookup_date_range(self, start: str, end: str) -> dict | None:
        entries = [t for t in self._timeline if start <= _to_full_date(t["date"]) <= end]
        label = f"{start} to {end}"
        logger.info("Date range query %s: %d matching days", label, len(entries))
        return _aggregate(entries, label)


sentiment_cache = SentimentCache()
