"""Semantic text splitter — context-aware document chunking."""
from __future__ import annotations

import re


class SemanticSplitter:
    """Split documents into semantically meaningful chunks.

    Splits on paragraph boundaries, headings, and natural breaks
    to preserve context within each chunk.
    """

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        """Split text into semantic chunks."""
        # Split on double newlines (paragraph boundaries)
        paragraphs = re.split(r"\n\n+", text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size, start new chunk
            if current_chunk and len(current_chunk) + len(para) + 2 > self.chunk_size:
                chunks.append(current_chunk.strip())
                # Keep overlap from end of current chunk
                if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                    current_chunk = current_chunk[-self.chunk_overlap:] + "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]
