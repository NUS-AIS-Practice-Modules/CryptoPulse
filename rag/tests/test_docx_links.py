import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.ingestion.docx_links import extract_docx_links


class DocxLinksTests(unittest.TestCase):
    def test_extracts_inline_and_relationship_links(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "links.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "word/document.xml",
                    """<?xml version="1.0" encoding="UTF-8"?>
                    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                      <w:body><w:p><w:r><w:t>https://example.test/a</w:t></w:r></w:p></w:body>
                    </w:document>""",
                )
                archive.writestr(
                    "word/_rels/document.xml.rels",
                    """<?xml version="1.0" encoding="UTF-8"?>
                    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                      <Relationship Id="rId1" Type="hyperlink" Target="https://example.test/b" TargetMode="External"/>
                    </Relationships>""",
                )

            self.assertEqual(
                extract_docx_links(path),
                ["https://example.test/b", "https://example.test/a"],
            )


if __name__ == "__main__":
    unittest.main()
