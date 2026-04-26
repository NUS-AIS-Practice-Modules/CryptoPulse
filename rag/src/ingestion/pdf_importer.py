from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .normalizer import normalize_documents, write_jsonl

MIN_TEXT_CHARS_BEFORE_OCR = 200


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract PDF text and normalize documents.")
    parser.add_argument("--manifest", required=True, help="JSONL manifest with path/source fields")
    parser.add_argument("--output", required=True, help="Normalized JSONL output path")
    args = parser.parse_args(argv)

    records = load_manifest(args.manifest)
    raw_documents = [record_to_raw_document(record) for record in records if _is_ok(record)]
    documents = normalize_documents(raw_documents)
    count = write_jsonl(documents, args.output)
    print(f"manifest_records={len(records)} normalized_documents={count}")
    return 0


def load_manifest(path: str | Path) -> list[dict[str, Any]]:
    manifest_path = Path(path)
    records = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid manifest JSON on line {line_number}") from exc
    return records


def record_to_raw_document(record: dict[str, Any]) -> dict[str, Any]:
    pdf_path = Path(record["path"])
    content = extract_pdf_text(pdf_path)
    metadata = dict(record.get("metadata") or {})
    metadata["url"] = record.get("url") or metadata.get("url") or str(pdf_path)
    metadata["published_at"] = (
        record.get("published_at")
        or metadata.get("published_at")
        or _mtime_as_utc(pdf_path)
    )
    metadata["language"] = metadata.get("language") or "en"
    metadata["entity_tags"] = metadata.get("entity_tags") or []
    metadata["source_id"] = metadata.get("source_id") or pdf_path.stem
    metadata["ingested_at"] = metadata.get("ingested_at") or _utc_now()
    metadata["local_path"] = str(pdf_path)

    return {
        "title": record.get("title") or pdf_path.stem,
        "content": content,
        "source": record["source"],
        "url": metadata["url"],
        "published_at": metadata["published_at"],
        "metadata": metadata,
    }


def extract_pdf_text(path: str | Path) -> str:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise ValueError(f"PDF path does not exist: {pdf_path}")

    with tempfile.NamedTemporaryFile(suffix=".txt") as output:
        subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), output.name],
            check=True,
            capture_output=True,
            text=True,
        )
        text = Path(output.name).read_text(encoding="utf-8", errors="replace")

    if len(text.strip()) >= MIN_TEXT_CHARS_BEFORE_OCR:
        return text
    return extract_pdf_text_with_ocr(pdf_path)


def extract_pdf_text_with_ocr(path: str | Path) -> str:
    pdf_path = Path(path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_prefix = str(Path(tmp_dir) / "page")
        subprocess.run(
            ["pdftoppm", "-r", "200", "-png", str(pdf_path), output_prefix],
            check=True,
            capture_output=True,
            text=True,
        )
        texts = []
        for image_path in sorted(Path(tmp_dir).glob("page-*.png")):
            result = subprocess.run(
                ["tesseract", str(image_path), "stdout", "-l", "eng"],
                check=True,
                capture_output=True,
                text=True,
            )
            page_text = result.stdout.strip()
            if page_text:
                texts.append(page_text)
        return "\n\n".join(texts)


def _is_ok(record: dict[str, Any]) -> bool:
    return record.get("status", "ok") == "ok"


def _mtime_as_utc(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
