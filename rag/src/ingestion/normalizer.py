from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


SOURCE_TYPES = {
    "whitepaper",
    "regulatory",
    "market_data",
    "case_study",
    "social_media",
    "news",
}

REQUIRED_METADATA_FIELDS = (
    "url",
    "published_at",
    "language",
    "source_id",
    "entity_tags",
    "ingested_at",
)


@dataclass(frozen=True)
class NormalizedDocument:
    title: str
    content: str
    source: str
    url: str
    published_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = html.unescape(str(value)).replace("\x00", " ")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_document(
    raw: Mapping[str, Any],
    *,
    default_source: str | None = None,
    ingested_at: str | None = None,
) -> NormalizedDocument:
    if not isinstance(raw, Mapping):
        raise ValueError("raw document must be a mapping")

    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), Mapping) else {}
    source = clean_text(raw.get("source") or metadata.get("source") or default_source)
    if source not in SOURCE_TYPES:
        raise ValueError(f"invalid document source: {source!r}")

    title = _first_clean(raw, metadata, ("title", "headline", "name"))
    content = _first_clean(raw, metadata, ("content", "text", "body", "summary"))
    if not title:
        raise ValueError("document title is required")
    if not content:
        raise ValueError("document content is required")

    url = _first_clean(raw, metadata, ("url", "link", "source_url"))
    published_at = _first_clean(raw, metadata, ("published_at", "created_at", "date"))
    if not published_at:
        published_at = _utc_now()

    normalized_metadata = dict(metadata)
    normalized_metadata["url"] = clean_text(normalized_metadata.get("url") or url)
    normalized_metadata["published_at"] = clean_text(
        normalized_metadata.get("published_at") or published_at
    )
    normalized_metadata["language"] = clean_text(
        normalized_metadata.get("language") or raw.get("language") or "en"
    )
    normalized_metadata["entity_tags"] = _normalize_tags(
        normalized_metadata.get("entity_tags") or raw.get("entity_tags") or raw.get("tags")
    )
    normalized_metadata["source_id"] = clean_text(
        normalized_metadata.get("source_id") or raw.get("source_id")
    ) or _build_source_id(source, url, title, content)
    normalized_metadata["ingested_at"] = clean_text(
        normalized_metadata.get("ingested_at") or ingested_at
    ) or _utc_now()

    return NormalizedDocument(
        title=title,
        content=content,
        source=source,
        url=url,
        published_at=published_at,
        metadata={field: normalized_metadata[field] for field in REQUIRED_METADATA_FIELDS},
    )


def normalize_documents(
    raw_documents: Iterable[Mapping[str, Any]],
    *,
    default_source: str | None = None,
    ingested_at: str | None = None,
    deduplicate: bool = True,
) -> list[NormalizedDocument]:
    documents: list[NormalizedDocument] = []
    seen: set[tuple[str, str]] = set()

    for raw in raw_documents:
        normalized = normalize_document(
            raw,
            default_source=default_source,
            ingested_at=ingested_at,
        )
        dedupe_key = (
            normalized.source,
            normalized.metadata["source_id"],
        )
        content_hash = hashlib.sha256(normalized.content.encode("utf-8")).hexdigest()
        if deduplicate and (dedupe_key in seen or (normalized.source, content_hash) in seen):
            continue
        seen.add(dedupe_key)
        seen.add((normalized.source, content_hash))
        documents.append(normalized)

    return documents


def load_raw_documents(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        raise ValueError(f"input path does not exist: {input_path}")

    if input_path.suffix.lower() == ".jsonl":
        documents = []
        with input_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    try:
                        documents.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSONL on line {line_number}") from exc
        return documents

    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("documents"), list):
        return data["documents"]
    raise ValueError("JSON input must be a list or an object with a documents list")


def write_jsonl(documents: Iterable[NormalizedDocument], path: str | Path) -> int:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize raw RAG documents to JSONL.")
    parser.add_argument("--input", required=True, help="Raw JSON or JSONL input file")
    parser.add_argument("--output", required=True, help="Normalized JSONL output file")
    parser.add_argument("--source", choices=sorted(SOURCE_TYPES), help="Default source")
    args = parser.parse_args(argv)

    raw_documents = load_raw_documents(args.input)
    documents = normalize_documents(raw_documents, default_source=args.source)
    count = write_jsonl(documents, args.output)
    print(f"normalized_documents={count}")
    return 0


def _first_clean(
    raw: Mapping[str, Any],
    metadata: Mapping[str, Any],
    field_names: tuple[str, ...],
) -> str:
    for field_name in field_names:
        value = raw.get(field_name)
        if value is None:
            value = metadata.get(field_name)
        cleaned = clean_text(value)
        if cleaned:
            return cleaned
    return ""


def _normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, Iterable):
        values = list(value)
    else:
        values = [value]
    return [tag for tag in (clean_text(item) for item in values) if tag]


def _build_source_id(source: str, url: str, title: str, content: str) -> str:
    stable_basis = f"{source}|{url or title}|{content[:240]}"
    digest = hashlib.sha256(stable_basis.encode("utf-8")).hexdigest()
    return digest[:16]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
