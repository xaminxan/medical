"""Triangulation engine — cross-comparison of parameters."""
from __future__ import annotations

from typing import Any


class TriangulationEngine:
    """Perform triangular cross-comparison of document parameters."""

    @staticmethod
    def vertical_compare(
        draft_params: dict[str, Any],
        truth_params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Compare draft parameters against ground truth (vertical).

        Returns:
            List of conflict dicts.
        """
        conflicts = []

        for param_name, draft_info in draft_params.items():
            if param_name in truth_params:
                truth_value = str(truth_params[param_name].get("value", "")).lower().strip()
                draft_value = str(draft_info.get("value", "")).lower().strip()

                if truth_value and draft_value and truth_value != draft_value:
                    conflicts.append({
                        "param_name": param_name,
                        "source_value": truth_params[param_name].get("value", ""),
                        "draft_value": draft_info.get("value", ""),
                        "comparison_type": "vertical",
                        "context": draft_info.get("source_context", ""),
                        "suggestion": f"Replace '{draft_info.get('value', '')}' with '{truth_params[param_name].get('value', '')}'",
                    })

        return conflicts

    @staticmethod
    def horizontal_compare(
        draft_params: dict[str, Any],
        other_docs_params: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Compare draft parameters against other generated documents (horizontal).

        Returns:
            List of conflict dicts.
        """
        conflicts = []

        for doc_name, doc_params in other_docs_params.items():
            for param_name, draft_info in draft_params.items():
                if param_name in doc_params:
                    other_value = str(doc_params[param_name].get("value", "")).lower().strip()
                    draft_value = str(draft_info.get("value", "")).lower().strip()

                    if other_value and draft_value and other_value != draft_value:
                        conflicts.append({
                            "param_name": param_name,
                            "source_value": doc_params[param_name].get("value", ""),
                            "draft_value": draft_info.get("value", ""),
                            "comparison_type": "horizontal",
                            "other_doc": doc_name,
                            "context": draft_info.get("source_context", ""),
                            "suggestion": f"Align with '{doc_name}': use '{doc_params[param_name].get('value', '')}'",
                        })

        return conflicts

    @staticmethod
    def full_triangulation(
        draft_params: dict[str, Any],
        truth_params: dict[str, Any],
        other_docs_params: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform full triangular cross-comparison.

        1. Vertical: draft vs truth
        2. Horizontal: draft vs other docs
        """
        conflicts = TriangulationEngine.vertical_compare(draft_params, truth_params)

        if other_docs_params:
            conflicts.extend(
                TriangulationEngine.horizontal_compare(draft_params, other_docs_params)
            )

        return conflicts
