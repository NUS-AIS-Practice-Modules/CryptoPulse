"""
Reddit Crypto Crawler for LoRA-001 / LoRA-002
==============================================
Collects unlabeled crypto-related posts & comments from Reddit for downstream
weak-supervision price-based labeling (see LORA-002).

Output schema (JSONL, one record per line):
    {
        "id":          str,        # Reddit fullname (unique)
        "source":      "reddit",
        "subreddit":   str,
        "kind":        "submission" | "comment",
        "author":      str,
        "created_utc": int,        # <-- required by LORA-002 price alignment
        "text":        str,        # cleaned
        "raw_text":    str,        # before cleaning (for audit)
        "score":       int,
        "num_comments":int | None, # submissions only
        "url":         str,
        "coins":       list[str],  # extracted tickers, e.g. ["BTC", "ETH"]
    }

Usage:
    # One-shot
    python reddit_crawler.py \
        --subreddits cryptocurrency bitcoin CryptoMarkets ethfinance \
        --limit 3000 \
        --mode new \
        --out data/raw/reddit_crypto.jsonl

    # Resume (skips IDs already in the output file)
    python reddit_crawler.py ... --resume

Dependencies:
    pip install praw python-dotenv tqdm

Credentials (.env file or env vars):
    REDDIT_CLIENT_ID=...
    REDDIT_CLIENT_SECRET=...
    REDDIT_USER_AGENT=crypto-lora-research/0.1 by u/your_username

How to get credentials:
    1. Go to https://www.reddit.com/prefs/apps
    2. Click "create another app..." -> type: "script"
    3. redirect uri: http://localhost:8080 (any valid URL)
    4. Copy client_id (under app name) and client_secret
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, Iterator, Optional

import praw
from praw.models import Submission, Comment
from prawcore.exceptions import PrawcoreException, TooManyRequests, ServerError
from tqdm import tqdm

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("reddit_crawler")


# --------------------------------------------------------------------------- #
# Coin ticker extraction
# --------------------------------------------------------------------------- #
# Keep this list aligned with what your CoinGecko price-fetcher supports.
# Add more as needed. Order matters only for debugging.
COIN_MAP: dict[str, str] = {
    # name / alias  ->  canonical ticker
    "bitcoin": "BTC", "btc": "BTC", "xbt": "BTC",
    "ethereum": "ETH", "eth": "ETH", "ether": "ETH",
    "solana": "SOL", "sol": "SOL",
    "ripple": "XRP", "xrp": "XRP",
    "cardano": "ADA", "ada": "ADA",
    "dogecoin": "DOGE", "doge": "DOGE",
    "binance": "BNB", "bnb": "BNB",
    "polkadot": "DOT", "dot": "DOT",
    "avalanche": "AVAX", "avax": "AVAX",
    "chainlink": "LINK", "link": "LINK",
    "polygon": "MATIC", "matic": "MATIC",
    "litecoin": "LTC", "ltc": "LTC",
    "shiba": "SHIB", "shib": "SHIB",
    "pepe": "PEPE",
    "tron": "TRX", "trx": "TRX",
}

# Compile once. Word-boundaries on both sides, case-insensitive.
# Also match $BTC, #BTC style mentions.
_COIN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[\$#]?(" + "|".join(re.escape(k) for k in COIN_MAP) + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

def extract_coins(text: str) -> list[str]:
    """Return unique canonical tickers mentioned in the text, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _COIN_PATTERN.finditer(text):
        ticker = COIN_MAP[m.group(1).lower()]
        if ticker not in seen:
            seen.add(ticker)
            out.append(ticker)
    return out


# --------------------------------------------------------------------------- #
# Text cleaning (matches LORA-001 validation: no URLs, no @mentions, etc.)
# --------------------------------------------------------------------------- #
_URL_RE      = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE  = re.compile(r"(?<![A-Za-z0-9])[@/]?u/[A-Za-z0-9_-]+", re.IGNORECASE)
_SUBREF_RE   = re.compile(r"(?<![A-Za-z0-9])/?r/[A-Za-z0-9_]+", re.IGNORECASE)
_WS_RE       = re.compile(r"\s+")
_INVISIBLE_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")

def clean_text(text: str) -> str:
    if not text:
        return ""
    t = _INVISIBLE_RE.sub("", text)
    t = _URL_RE.sub(" ", t)
    t = _MENTION_RE.sub(" ", t)
    t = _SUBREF_RE.sub(" ", t)
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = _WS_RE.sub(" ", t).strip()
    return t


def is_valid_text(text: str, min_words: int = 4) -> bool:
    """LORA-001 says: drop short texts (<4 words)."""
    if not text:
        return False
    if text.lower().strip() in {"[deleted]", "[removed]"}:
        return False
    return len(text.split()) >= min_words


# --------------------------------------------------------------------------- #
# Record
# --------------------------------------------------------------------------- #
@dataclass
class RedditRecord:
    id: str
    source: str
    subreddit: str
    kind: str
    author: str
    created_utc: int
    text: str
    raw_text: str
    score: int
    num_comments: Optional[int]
    url: str
    coins: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Reddit client
# --------------------------------------------------------------------------- #
def build_reddit() -> praw.Reddit:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "crypto-lora-research/0.1")
    if not (client_id and client_secret):
        log.error("Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET. "
                  "Set them in env or a .env file.")
        sys.exit(1)
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        ratelimit_seconds=60,   # PRAW will sleep up to 60s if hit
    )
    reddit.read_only = True
    log.info(f"Reddit client built. read_only={reddit.read_only}")
    return reddit


# --------------------------------------------------------------------------- #
# Crawl logic
# --------------------------------------------------------------------------- #
def iter_submissions(
    reddit: praw.Reddit,
    subreddit: str,
    limit: int,
    mode: str,
) -> Iterator[Submission]:
    sub = reddit.subreddit(subreddit)
    if mode == "new":
        return sub.new(limit=limit)
    if mode == "hot":
        return sub.hot(limit=limit)
    if mode == "top":
        return sub.top(time_filter="month", limit=limit)
    raise ValueError(f"Unknown mode: {mode}")


def submission_to_record(s: Submission) -> Optional[RedditRecord]:
    raw = (s.title or "") + "\n" + (s.selftext or "")
    cleaned = clean_text(raw)
    if not is_valid_text(cleaned):
        return None
    return RedditRecord(
        id=s.fullname,
        source="reddit",
        subreddit=str(s.subreddit),
        kind="submission",
        author=str(s.author) if s.author else "[deleted]",
        created_utc=int(s.created_utc),
        text=cleaned,
        raw_text=raw,
        score=int(s.score),
        num_comments=int(s.num_comments),
        url=f"https://reddit.com{s.permalink}",
        coins=extract_coins(cleaned),
    )


def comment_to_record(c: Comment, subreddit_name: str) -> Optional[RedditRecord]:
    cleaned = clean_text(c.body or "")
    if not is_valid_text(cleaned):
        return None
    return RedditRecord(
        id=c.fullname,
        source="reddit",
        subreddit=subreddit_name,
        kind="comment",
        author=str(c.author) if c.author else "[deleted]",
        created_utc=int(c.created_utc),
        text=cleaned,
        raw_text=c.body or "",
        score=int(c.score),
        num_comments=None,
        url=f"https://reddit.com{c.permalink}",
        coins=extract_coins(cleaned),
    )


def crawl_subreddit(
    reddit: praw.Reddit,
    subreddit: str,
    submission_limit: int,
    mode: str,
    include_comments: bool,
    comments_per_post: int,
    seen: set[str],
) -> Iterator[RedditRecord]:
    """Yield records from one subreddit. Robust to transient errors."""
    log.info(f"[{subreddit}] starting (mode={mode}, limit={submission_limit})")
    pbar = tqdm(desc=f"r/{subreddit}", total=submission_limit, unit="post")

    try:
        for s in iter_submissions(reddit, subreddit, submission_limit, mode):
            pbar.update(1)
            try:
                if s.fullname in seen:
                    continue
                rec = submission_to_record(s)
                if rec is not None:
                    seen.add(rec.id)
                    yield rec

                if include_comments and s.num_comments > 0:
                    # Only expand top-level to cap fan-out; "more" is expensive.
                    s.comments.replace_more(limit=0)
                    for i, c in enumerate(s.comments.list()):
                        if i >= comments_per_post:
                            break
                        if not isinstance(c, Comment):
                            continue
                        if c.fullname in seen:
                            continue
                        crec = comment_to_record(c, str(s.subreddit))
                        if crec is not None:
                            seen.add(crec.id)
                            yield crec

            except TooManyRequests:
                log.warning("429 rate-limited; sleeping 30s")
                time.sleep(30)
            except ServerError:
                log.warning("Reddit 5xx; sleeping 10s")
                time.sleep(10)
            except PrawcoreException as e:
                log.warning(f"prawcore error on {s.id}: {e}")
                time.sleep(2)
    finally:
        pbar.close()


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def load_seen_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["id"])
            except Exception:
                continue
    log.info(f"Resume: loaded {len(seen)} existing IDs from {path}")
    return seen


def append_records(records: Iterable[RedditRecord], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
            n += 1
    return n


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser(description="Reddit crypto crawler for LoRA training data.")
    p.add_argument("--subreddits", nargs="+",
                   default=["cryptocurrency", "bitcoin", "CryptoMarkets", "ethfinance"],
                   help="Subreddits to crawl.")
    p.add_argument("--limit", type=int, default=1000,
                   help="Submissions per subreddit.")
    p.add_argument("--mode", choices=["new", "hot", "top"], default="new",
                   help="Listing type. 'new' gives best time-coverage for weak supervision.")
    p.add_argument("--no-comments", action="store_true",
                   help="Skip comment expansion (faster, submission-only).")
    p.add_argument("--comments-per-post", type=int, default=20,
                   help="Max top-level comments per submission.")
    p.add_argument("--out", type=Path, default=Path("data/raw/reddit_crypto.jsonl"))
    p.add_argument("--resume", action="store_true",
                   help="Skip IDs already present in the output file.")
    p.add_argument("--require-coin", action="store_true",
                   help="Only keep records with at least one recognized ticker. "
                        "Recommended for weak-supervision downstream.")
    args = p.parse_args()

    reddit = build_reddit()
    seen = load_seen_ids(args.out) if args.resume else set()

    total_written = 0
    for sr in args.subreddits:
        batch: list[RedditRecord] = []
        for rec in crawl_subreddit(
            reddit=reddit,
            subreddit=sr,
            submission_limit=args.limit,
            mode=args.mode,
            include_comments=not args.no_comments,
            comments_per_post=args.comments_per_post,
            seen=seen,
        ):
            if args.require_coin and not rec.coins:
                continue
            batch.append(rec)
            # Flush every 500 records to limit memory and enable mid-run inspection.
            if len(batch) >= 500:
                total_written += append_records(batch, args.out)
                batch.clear()
        if batch:
            total_written += append_records(batch, args.out)
        log.info(f"[{sr}] done. running total written = {total_written}")

    log.info(f"✅ Finished. {total_written} new records appended to {args.out}")


if __name__ == "__main__":
    main()