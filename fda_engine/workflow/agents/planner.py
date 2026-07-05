"""Planner agent — determines document generation order based on dependencies."""
from __future__ import annotations

from loguru import logger

from fda_engine.workflow.state import WorkflowState


def planner_node(state: WorkflowState) -> dict:
    """Plan the document generation order based on the FDA tree.

    Analyzes dependencies and required nodes to build an execution queue.
    """
    logger.info("Planner: analyzing document tree...")

    tree = state.doc_tree
    if not tree:
        return {"status": "error", "error": "No document tree provided"}

    queue = _plan_generation_order(tree, state.resolved_params)

    if not queue:
        return {"status": "completed"}

    return {
        "generation_queue": queue,
        "current_node": queue[0] if queue else "",
        "status": "generating",
    }


def _plan_generation_order(tree: dict, resolved_params: dict) -> list[str]:
    """Determine generation order: required nodes first, then by depth."""
    nodes = []
    _collect_nodes(tree, nodes, resolved_params, depth=0)
    nodes.sort(key=lambda n: (not n["required"], n["depth"]))
    return [n["node_id"] for n in nodes]


def _collect_nodes(node: dict, result: list, resolved_params: dict, depth: int = 0):
    """Recursively collect all nodes with metadata."""
    node_id = node.get("node_id", "")
    if node_id and node_id != "root":
        result.append({
            "node_id": node_id,
            "title": node.get("title", ""),
            "required": node.get("required", True),
            "description": node.get("description", ""),
            "depth": depth,
            "has_resolved_params": node_id in resolved_params,
        })
    for child in node.get("children", []):
        _collect_nodes(child, result, resolved_params, depth + 1)
