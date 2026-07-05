"""Reviewer agent — extracts parameters and checks consistency."""
from __future__ import annotations

from loguru import logger

from fda_engine.workflow.state import WorkflowState


def reviewer_node(state: WorkflowState) -> dict:
    """Review the generated document for parameter consistency.

    1. Extract parameters from the draft
    2. Compare against truth params (vertical)
    3. Compare against other docs (horizontal)
    4. Return conflicts if any
    """
    node_id = state.current_node
    if not node_id:
        return {"conflict_list": [], "status": "completed"}

    logger.info(f"Reviewer: checking '{node_id}'...")

    draft_content = state.drafts.get(node_id, "")
    if not draft_content:
        return {"conflict_list": [], "status": "generating"}

    # Extract parameters from draft (using regex patterns)
    from fda_engine.verification.entity_extractor import EntityExtractor
    extractor = EntityExtractor()
    draft_params = extractor.extract(draft_content)

    # Vertical comparison: draft vs truth
    from fda_engine.verification.triangulation import TriangulationEngine
    conflicts = TriangulationEngine.vertical_compare(draft_params, state.truth_params)

    # Horizontal comparison: draft vs other generated docs
    other_params = {
        doc_id: state.extracted_params.get(doc_id, {})
        for doc_id in state.drafts
        if doc_id != node_id and not doc_id.startswith("_")
    }
    if other_params:
        conflicts.extend(
            TriangulationEngine.horizontal_compare(draft_params, other_params)
        )

    # Add doc_id to each conflict
    for conflict in conflicts:
        conflict["doc_id"] = node_id

    status = "generating" if not conflicts else "verifying"

    return {
        "conflict_list": conflicts,
        "extracted_params": {
            **state.extracted_params,
            node_id: draft_params,
        },
        "current_node": state.generation_queue[1] if len(state.generation_queue) > 1 else "",
        "generation_queue": state.generation_queue[1:] if len(state.generation_queue) > 1 else [],
        "status": status,
    }
