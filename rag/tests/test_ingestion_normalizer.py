import json
import tempfile
import unittest
from pathlib import Path

from src.ingestion import (
    REQUIRED_METADATA_FIELDS,
    SOURCE_TYPES,
    clean_text,
    load_raw_documents,
    normalize_document,
    normalize_documents,
    write_jsonl,
)


FIXED_INGESTED_AT = "2026-04-25T00:00:00Z"


def raw_document(source: str, title: str | None = None, content: str | None = None) -> dict:
    return {
        "title": title or f"{source} title",
        "content": content or f"{source} content about Bitcoin liquidity and market risk.",
        "source": source,
        "url": f"https://example.test/{source}",
        "published_at": "2026-04-20T00:00:00Z",
        "language": "en",
        "entity_tags": ["BTC", "Bitcoin"],
    }


class IngestionNormalizerTests(unittest.TestCase):
    def test_normalizes_all_required_sources_with_metadata_fields(self) -> None:
        raw_documents = [raw_document(source) for source in sorted(SOURCE_TYPES)]

        documents = normalize_documents(raw_documents, ingested_at=FIXED_INGESTED_AT)

        self.assertEqual(len(documents), 6)
        self.assertEqual({document.source for document in documents}, SOURCE_TYPES)
        for document in documents:
            payload = document.to_dict()
            self.assertEqual(
                {"title", "content", "source", "url", "published_at", "metadata"},
                set(payload),
            )
            self.assertEqual(set(REQUIRED_METADATA_FIELDS), set(document.metadata))
            self.assertEqual(document.metadata["ingested_at"], FIXED_INGESTED_AT)
            self.assertEqual(document.metadata["url"], document.url)
            self.assertEqual(document.metadata["published_at"], document.published_at)

    def test_cleans_html_noise_and_normalizes_tags(self) -> None:
        document = normalize_document(
            {
                "headline": " BTC update ",
                "body": "<script>bad()</script><p>Bitcoin&nbsp;ETF\n\nflows</p>",
                "source": "news",
                "url": "https://example.test/news",
                "published_at": "2026-04-21T00:00:00Z",
                "tags": "BTC, ETF, ",
            },
            ingested_at=FIXED_INGESTED_AT,
        )

        self.assertEqual(document.title, "BTC update")
        self.assertEqual(document.content, "Bitcoin ETF flows")
        self.assertEqual(document.metadata["entity_tags"], ["BTC", "ETF"])
        self.assertEqual(clean_text("<b>hello</b>\n world"), "hello world")

    def test_deduplicates_by_source_id_or_content_hash(self) -> None:
        first = raw_document("case_study", title="FTX collapse")
        duplicate_url = raw_document("case_study", title="FTX collapse revised")
        duplicate_content = raw_document("case_study", title="Different title")
        duplicate_content["url"] = "https://example.test/case_study-copy"
        duplicate_content["content"] = first["content"]

        documents = normalize_documents(
            [first, duplicate_url, duplicate_content],
            ingested_at=FIXED_INGESTED_AT,
        )

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].title, "FTX collapse")

    def test_rejects_invalid_source_and_missing_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid document source"):
            normalize_document({"title": "X", "content": "Y", "source": "blog"})

        with self.assertRaisesRegex(ValueError, "document content is required"):
            normalize_document({"title": "X", "source": "news"})

    def test_loads_json_and_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "raw.json"
            output_path = Path(tmp_dir) / "normalized.jsonl"
            input_path.write_text(json.dumps([raw_document("whitepaper")]), encoding="utf-8")

            loaded = load_raw_documents(input_path)
            documents = normalize_documents(loaded, ingested_at=FIXED_INGESTED_AT)
            count = write_jsonl(documents, output_path)

            self.assertEqual(count, 1)
            line = output_path.read_text(encoding="utf-8").strip()
            self.assertEqual(json.loads(line)["source"], "whitepaper")


if __name__ == "__main__":
    unittest.main()
