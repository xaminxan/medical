"""Workspace ingestion — parse and index technical documents."""
from __future__ import annotations

from pathlib import Path

from loguru import logger


async def index_workspace(folder: Path, config) -> int:
    """Index all documents in a workspace folder.

    Parses PDFs, Markdown, and text files, then stores them
    for RAG retrieval (ChromaDB integration in Phase 2).

    Returns:
        Number of documents indexed.
    """
    count = 0
    for ext in ("*.md", "*.txt", "*.csv", "*.pdf", "*.docx"):
        for f in folder.rglob(ext):
            try:
                content = _parse_file(f)
                if content:
                    count += 1
                    logger.debug(f"Indexed: {f.name} ({len(content)} chars)")
            except Exception as e:
                logger.warning(f"Failed to parse {f}: {e}")

    logger.info(f"Indexed {count} documents from {folder}")
    return count


def _parse_file(path: Path) -> str:
    """Parse a single file into text."""
    suffix = path.suffix.lower()

    if suffix in (".md", ".txt", ".csv"):
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            import pymupdf
            doc = pymupdf.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            logger.warning("pymupdf not installed, skipping PDF")
            return ""

    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not installed, skipping DOCX")
            return ""

    return ""
