import json
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "sentiment_data.json"


def _aggregate_records(records: list[dict], label: str) -> dict | None:
    if not records:
        return None
    bullish = sum(1 for r in records if r["output"] == "Bullish")
    bearish = sum(1 for r in records if r["output"] == "Bearish")
    neutral = sum(1 for r in records if r["output"] == "Neutral")
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


def _aggregate_timeline(entries: list[dict], label: str) -> dict | None:
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
        self._timeline: list[dict] = []           # global daily aggregates
        self._coin_records: dict[str, list[dict]] = defaultdict(list)  # coin → raw records

    def load(self, summary_path: str) -> None:
        # Load global timeline (sentiment_summary.json)
        p = Path(summary_path)
        if not p.exists():
            logger.warning("sentiment_summary.json not found at %s", summary_path)
        else:
            self._timeline = json.loads(p.read_text(encoding="utf-8"))
            logger.info("Loaded global timeline: %d days", len(self._timeline))

        # Load per-coin records (sentiment_data.json)
        if _DATA_FILE.exists():
            records = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
            for r in records:
                if r.get("coin"):
                    self._coin_records[r["coin"]].append(r)
            logger.info("Loaded coin records: %s", {c: len(v) for c, v in self._coin_records.items()})

    def lookup_date_range(self, start: str, end: str) -> dict | None:
        entries = [t for t in self._timeline if start <= f"2026-{t['date']}" <= end]
        label = f"{start} to {end}"
        logger.info("Global sentiment query %s: %d matching days", label, len(entries))
        return _aggregate_timeline(entries, label)

    def lookup_coin_date_range(self, coin: str, start: str, end: str) -> dict | None:
        records = [r for r in self._coin_records.get(coin.upper(), []) if start <= r["date"] <= end]
        label = f"{coin} {start} to {end}"
        logger.info("Coin sentiment query %s: %d matching records", label, len(records))
        return _aggregate_records(records, label)


sentiment_cache = SentimentCache()
