from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
RELATIONSHIP_NAMESPACE = {
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships"
}
URL_RE = re.compile(r"https?://[^\s<>\"]+")


def extract_docx_links(path: str | Path) -> list[str]:
    docx_path = Path(path)
    if not docx_path.exists():
        raise ValueError(f"DOCX path does not exist: {docx_path}")

    links: list[str] = []
    with zipfile.ZipFile(docx_path) as archive:
        links.extend(_relationship_links(archive))
        links.extend(_inline_text_links(archive))
    return _dedupe_links(links)


def _relationship_links(archive: zipfile.ZipFile) -> list[str]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in archive.namelist():
        return []

    root = ElementTree.fromstring(archive.read(rels_path))
    links = []
    for relationship in root.findall("rel:Relationship", RELATIONSHIP_NAMESPACE):
        target = relationship.attrib.get("Target", "")
        if target.startswith(("http://", "https://")):
            links.append(target)
    return links


def _inline_text_links(archive: zipfile.ZipFile) -> list[str]:
    document_path = "word/document.xml"
    if document_path not in archive.namelist():
        return []

    root = ElementTree.fromstring(archive.read(document_path))
    links = []
    for text_node in root.findall(".//w:t", WORD_NAMESPACE):
        if text_node.text:
            links.extend(URL_RE.findall(text_node.text))
    return links


def _dedupe_links(links: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for link in links:
        cleaned = link.rstrip(").,;]")
        if cleaned and cleaned not in seen:
            unique.append(cleaned)
            seen.add(cleaned)
    return unique
