"""Writer agent — generates document content using LLM + RAG context."""
from __future__ import annotations

from loguru import logger

from fda_engine.workflow.state import WorkflowState


def writer_node(state: WorkflowState) -> dict:
    """Generate content for the current document node.

    This is a synchronous wrapper for the LangGraph state machine.
    The actual LLM generation happens via the FDAEngine in the API layer.
    """
    node_id = state.current_node
    if not node_id:
        return {"status": "completed"}

    logger.info(f"Writer: generating '{node_id}'...")

    # Find node info from tree
    node_info = _find_node_in_tree(state.doc_tree, node_id)
    if not node_info:
        logger.warning(f"Node '{node_id}' not found in tree")
        return {"status": "generating"}

    # Build system prompt
    system_prompt = _build_system_prompt(node_id, node_info)

    # Get RAG context if available
    rag_context = state.drafts.get(f"_context_{node_id}", "")

    # The actual generation is handled by FDAEngine in the async API layer
    # This node just prepares the prompt and marks the status
    return {
        "drafts": {
            **state.drafts,
            f"_prompt_{node_id}": system_prompt,
        },
        "status": "verifying",
    }


def _find_node_in_tree(tree: dict, node_id: str) -> dict | None:
    """Find a node by ID in the tree."""
    if tree.get("node_id") == node_id:
        return tree
    for child in tree.get("children", []):
        found = _find_node_in_tree(child, node_id)
        if found:
            return found
    return None


def _build_system_prompt(node_id: str, node_info: dict) -> str:
    """Build the system prompt for document generation."""
    title = node_info.get("title", node_id)
    description = node_info.get("description", "")

    return (
        "You are a senior FDA regulatory affairs specialist with expertise in 510(k) submissions.\n\n"
        f"TASK: Generate the '{title}' section for a 510(k) premarket notification.\n\n"
        f"DESCRIPTION: {description}\n\n"
        "REQUIREMENTS:\n"
        "- Write in formal, professional regulatory language\n"
        "- Use precise technical terminology\n"
        "- Follow FDA guidance documents and 21 CFR requirements\n"
        "- Reference applicable standards (ISO, IEC, ASTM, etc.)\n"
        "- Include specific product parameters where applicable\n"
        "- Do not fabricate data — use only provided reference materials\n"
        "- Structure the document with clear headings and paragraphs\n"
        "- Ensure consistency with other sections of the submission\n\n"
        "OUTPUT FORMAT:\n"
        "- Start with a clear section heading\n"
        "- Use numbered subsections where appropriate\n"
        "- Include references to standards and regulations\n"
        "- End with any applicable conclusions or statements"
    )
