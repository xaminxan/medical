"""Cascade updater — propagate parameter changes to all affected documents using LLM."""
from __future__ import annotations

from typing import Any, Callable

from loguru import logger


class CascadeUpdater:
    """Update documents after conflict resolution with LLM-powered rewriting."""

    def __init__(self):
        self.update_log: list[dict[str, Any]] = []

    async def cascade_update(
        self,
        old_value: str,
        new_value: str,
        param_name: str,
        generated_docs: dict[str, str],
        rewrite_fn: Callable | None = None,
    ) -> dict[str, Any]:
        """Replace old_value with new_value in all affected documents.

        Uses LLM rewriting when rewrite_fn is provided, otherwise falls back
        to simple text replacement.

        Args:
            old_value: The value to replace.
            new_value: The replacement value.
            param_name: Name of the parameter being updated.
            generated_docs: Dict of {doc_id: content}.
            rewrite_fn: Optional async function for LLM-powered rewriting.

        Returns:
            Summary of updates performed.
        """
        docs_updated = 0
        errors = []

        for doc_id, content in list(generated_docs.items()):
            if old_value.lower() not in content.lower():
                continue

            logger.info(f"Cascade: updating '{doc_id}' — replacing '{old_value}' with '{new_value}'")

            try:
                if rewrite_fn:
                    new_content = await rewrite_fn(
                        original_paragraph=content,
                        old_value=old_value,
                        new_value=new_value,
                        context=f"Parameter: {param_name}",
                    )
                else:
                    # Simple text replacement fallback
                    new_content = content.replace(old_value, new_value)
                    # Also try case-insensitive replacement
                    import re
                    pattern = re.compile(re.escape(old_value), re.IGNORECASE)
                    new_content = pattern.sub(new_value, content)

                generated_docs[doc_id] = new_content
                docs_updated += 1

                self.update_log.append({
                    "doc_id": doc_id,
                    "param_name": param_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "status": "success",
                })
            except Exception as e:
                logger.error(f"Failed to update '{doc_id}': {e}")
                errors.append({"doc_id": doc_id, "error": str(e)})

        logger.info(f"Cascade complete: {docs_updated} documents updated for '{param_name}'")
        return {
            "param_name": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "documents_updated": docs_updated,
            "errors": errors,
        }

    async def cascade_update_all(
        self,
        resolved_params: dict[str, Any],
        truth_params: dict[str, Any],
        generated_docs: dict[str, str],
        rewrite_fn: Callable | None = None,
    ) -> list[dict[str, Any]]:
        """Apply all resolved parameter changes to generated documents.

        Args:
            resolved_params: Dict of {param_name: new_value} from human resolution.
            truth_params: The current truth parameter matrix.
            generated_docs: Dict of {doc_id: content}.
            rewrite_fn: Optional async function for LLM-powered rewriting.

        Returns:
            List of update summaries.
        """
        results = []

        for param_name, new_value in resolved_params.items():
            old_value = truth_params.get(param_name, {}).get("value", "")
            if old_value and old_value != new_value:
                result = await self.cascade_update(
                    old_value=old_value,
                    new_value=new_value,
                    param_name=param_name,
                    generated_docs=generated_docs,
                    rewrite_fn=rewrite_fn,
                )
                results.append(result)

        return results

    def get_update_log(self) -> list[dict[str, Any]]:
        """Return the full update log."""
        return list(self.update_log)

    def clear_log(self):
        """Clear the update log."""
        self.update_log.clear()
