"""Arbiter agent — handles conflict resolution and cascade updates."""
from __future__ import annotations

from loguru import logger

from fda_engine.workflow.state import WorkflowState


def arbiter_node(state: WorkflowState) -> dict:
    """Handle conflict resolution.

    In interactive mode: pauses and waits for human input via API.
    In auto mode: applies the most common value or truth value.
    """
    logger.info(f"Arbiter: resolving {len(state.conflict_list)} conflicts...")

    if state.mode == "interactive":
        # In interactive mode, the API will handle human input
        # and call the resolver to update state
        return {"status": "blocked"}

    # Auto-resolve: prefer truth value for vertical conflicts
    resolved = dict(state.resolved_params)
    remaining_conflicts = []

    for conflict in state.conflict_list:
        param_name = conflict.get("param_name", "")
        comparison_type = conflict.get("comparison_type", "")

        if comparison_type == "vertical":
            # Use truth value (source is authoritative)
            resolved[param_name] = conflict.get("source_value", "")
            logger.info(f"Auto-resolved '{param_name}': using truth value '{conflict.get('source_value', '')}'")
        else:
            # Horizontal conflicts need human input or more context
            remaining_conflicts.append(conflict)

    if remaining_conflicts:
        logger.warning(f"{len(remaining_conflicts)} horizontal conflicts remain unresolved")
        return {
            "resolved_params": resolved,
            "conflict_list": remaining_conflicts,
            "status": "blocked",
        }

    return {
        "resolved_params": resolved,
        "conflict_list": [],
        "status": "generating",
    }
