"""Hybrid retriever — LlamaIndex-based retrieval with optional BM25."""
from __future__ import annotations

from typing import Any

from loguru import logger


class HybridRetriever:
    """Hybrid retrieval combining vector similarity and keyword matching."""

    def __init__(self, rag_engine):
        self.rag_engine = rag_engine

    async def retrieve(
        self,
        question: str,
        space: str = "product_tech",
        n_results: int = 5,
        filters: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents using hybrid search.

        Uses LlamaIndex vector retrieval as primary method.
        """
        results = await self.rag_engine.query(
            space=space,
            question=question,
            n_results=n_results,
            where=filters,
        )

        logger.debug(f"Retrieved {len(results)} results from '{space}'")
        return results

    async def retrieve_for_verification(
        self,
        param_name: str,
        param_value: str,
        space: str = "product_tech",
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve documents relevant to a specific parameter."""
        query = f"{param_name}: {param_value}"
        return await self.retrieve(query, space=space, n_results=n_results)

    async def retrieve_cross_doc(
        self,
        question: str,
        exclude_doc_id: str | None = None,
        space: str = "product_tech",
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve from other documents (horizontal comparison)."""
        results = await self.rag_engine.query(
            space=space,
            question=question,
            n_results=n_results,
        )

        # Filter out the source document if specified
        if exclude_doc_id:
            results = [
                r for r in results
                if r.get("metadata", {}).get("doc_id") != exclude_doc_id
            ]

        return results
