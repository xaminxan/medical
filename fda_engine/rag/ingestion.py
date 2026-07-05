"""Ingestion pipeline — LlamaIndex-based document parsing, chunking, and indexing."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger


class IngestionPipeline:
    """Pipeline for ingesting documents into the RAG engine using LlamaIndex."""

    def __init__(self, rag_engine):
        self.rag_engine = rag_engine
        self._splitter = None

    def _get_splitter(self):
        """Get or create the semantic text splitter."""
        if self._splitter is None:
            from llama_index.core.node_parser import SentenceSplitter

            self._splitter = SentenceSplitter(
                chunk_size=1024,
                chunk_overlap=128,
            )
        return self._splitter

    async def ingest_folder(
        self,
        folder: Path,
        space: str = "product_tech",
    ) -> int:
        """Ingest all documents from a folder.

        Returns:
            Number of documents ingested.
        """
        count = 0
        for ext in ("*.md", "*.txt", "*.csv", "*.pdf", "*.docx"):
            for f in folder.rglob(ext):
                try:
                    documents = self._parse_file(f)
                    if documents:
                        await self.rag_engine.add_documents_batch(space, documents)
                        count += len(documents)
                        logger.debug(f"Ingested: {f.name} ({len(documents)} chunks)")
                except Exception as e:
                    logger.warning(f"Failed to ingest {f}: {e}")

        logger.info(f"Ingested {count} document chunks into '{space}'")
        return count

    async def ingest_file(
        self,
        path: Path,
        space: str = "product_tech",
    ) -> int:
        """Ingest a single file."""
        documents = self._parse_file(path)
        if documents:
            await self.rag_engine.add_documents_batch(space, documents)
            return len(documents)
        return 0

    def _parse_file(self, path: Path) -> list[dict[str, Any]]:
        """Parse a file into document chunks."""
        suffix = path.suffix.lower()

        if suffix in (".md", ".txt", ".csv"):
            return self._parse_text(path)
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        elif suffix == ".docx":
            return self._parse_docx(path)

        return []

    def _parse_text(self, path: Path) -> list[dict[str, Any]]:
        """Parse text files with semantic chunking."""
        content = path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            return []

        chunks = self._chunk_text(content)
        return [
            {
                "doc_id": f"{path.stem}_chunk_{i}",
                "content": chunk,
                "metadata": {
                    "source": str(path),
                    "format": path.suffix,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

    def _parse_pdf(self, path: Path) -> list[dict[str, Any]]:
        """Parse PDF with page-aware chunking."""
        try:
            import pymupdf
            doc = pymupdf.open(str(path))
            documents = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                if not text.strip():
                    continue

                chunks = self._chunk_text(text)
                for i, chunk in enumerate(chunks):
                    documents.append({
                        "doc_id": f"{path.stem}_p{page_num + 1}_chunk_{i}",
                        "content": chunk,
                        "metadata": {
                            "source": str(path),
                            "format": "pdf",
                            "page": page_num + 1,
                            "chunk_index": i,
                        },
                    })

            return documents
        except ImportError:
            logger.warning("pymupdf not installed, skipping PDF")
            return []

    def _parse_docx(self, path: Path) -> list[dict[str, Any]]:
        """Parse DOCX with paragraph-aware chunking."""
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)

            if not content:
                return []

            chunks = self._chunk_text(content)
            return [
                {
                    "doc_id": f"{path.stem}_chunk_{i}",
                    "content": chunk,
                    "metadata": {
                        "source": str(path),
                        "format": "docx",
                        "chunk_index": i,
                    },
                }
                for i, chunk in enumerate(chunks)
            ]
        except ImportError:
            logger.warning("python-docx not installed, skipping DOCX")
            return []

    def _chunk_text(self, text: str, chunk_size: int = 1024, overlap: int = 128) -> list[str]:
        """Split text into semantic chunks."""
        if len(text) <= chunk_size:
            return [text]

        # Split on paragraph boundaries first
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current and len(current) + len(para) + 2 > chunk_size:
                chunks.append(current)
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para

        if current:
            chunks.append(current)

        return chunks if chunks else [text]
