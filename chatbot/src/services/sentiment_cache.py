import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


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
        if not recent:
            return None
        bullish = sum(t["bullish"] for t in recent)
        bearish = sum(t["bearish"] for t in recent)
        neutral = sum(t["neutral"] for t in recent)
        total = bullish + bearish + neutral or 1
        overall = max(("Bullish", bullish), ("Bearish", bearish), ("Neutral", neutral), key=lambda x: x[1])[0]
        return {
            "overall": overall,
            "bullish": bullish / total,
            "bearish": bearish / total,
            "neutral": neutral / total,
            "sample_count": total,
            "period": period,
        }


sentiment_cache = SentimentCache()
