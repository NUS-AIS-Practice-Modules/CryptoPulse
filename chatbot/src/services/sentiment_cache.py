import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SentimentCache:
    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def load(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            logger.warning("sentiment_summary.json not found at %s — sentiment lookup disabled", path)
            return
        with p.open(encoding="utf-8") as f:
            self._data = json.load(f)
        logger.info("Loaded sentiment cache: %d cryptos from %s", len(self._data), path)

    def lookup(self, crypto: str) -> dict | None:
        return self._data.get(crypto.upper())


sentiment_cache = SentimentCache()
