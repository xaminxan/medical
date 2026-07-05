"""Multi-format document parser for FDA technical files."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class DocumentParser:
    """Parse various document formats into structured text."""

    @staticmethod
    def parse(path: Path) -> dict[str, Any]:
        """Parse a document and return structured content."""
        suffix = path.suffix.lower()

        if suffix in (".md", ".txt", ".csv"):
            return {
                "path": str(path),
                "type": "text",
                "content": path.read_text(encoding="utf-8", errors="ignore"),
            }

        if suffix == ".pdf":
            return DocumentParser._parse_pdf(path)

        if suffix == ".docx":
            return DocumentParser._parse_docx(path)

        return {"path": str(path), "type": "unknown", "content": ""}

    @staticmethod
    def _parse_pdf(path: Path) -> dict[str, Any]:
        try:
            import pymupdf
            doc = pymupdf.open(str(path))
            pages = []
            for i, page in enumerate(doc):
                pages.append({
                    "page_num": i + 1,
                    "text": page.get_text(),
                })
            return {
                "path": str(path),
                "type": "pdf",
                "content": "\n".join(p["text"] for p in pages),
                "pages": len(pages),
            }
        except ImportError:
            return {"path": str(path), "type": "pdf", "content": "", "error": "pymupdf not installed"}

    @staticmethod
    def _parse_docx(path: Path) -> dict[str, Any]:
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs]
            return {
                "path": str(path),
                "type": "docx",
                "content": "\n".join(paragraphs),
                "paragraph_count": len(paragraphs),
            }
        except ImportError:
            return {"path": str(path), "type": "docx", "content": "", "error": "python-docx not installed"}
