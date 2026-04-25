"""Document ingestion and normalization utilities."""

from .normalizer import (
    REQUIRED_METADATA_FIELDS,
    SOURCE_TYPES,
    NormalizedDocument,
    clean_text,
    load_raw_documents,
    normalize_document,
    normalize_documents,
    write_jsonl,
)
from .docx_links import extract_docx_links

__all__ = [
    "REQUIRED_METADATA_FIELDS",
    "SOURCE_TYPES",
    "NormalizedDocument",
    "clean_text",
    "extract_docx_links",
    "load_raw_documents",
    "normalize_document",
    "normalize_documents",
    "write_jsonl",
]
