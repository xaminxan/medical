"""StateGraph construction and compilation."""
from __future__ import annotations

from fda_engine.workflow.state import WorkflowState


def build_workflow_graph():
    """Build the LangGraph StateGraph for FDA document generation.

    Graph topology:
        START -> planner -> writer -> reviewer -> {no conflicts: next/complete, conflicts: arbiter}
        arbiter -> (human resolve) -> writer (rewrite) -> reviewer (verify)

    Returns:
        Compiled StateGraph (requires langgraph to be installed).
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        raise ImportError("langgraph is required: pip install langgraph")

    from fda_engine.workflow.agents.planner import planner_node
    from fda_engine.workflow.agents.writer import writer_node
    from fda_engine.workflow.agents.reviewer import reviewer_node
    from fda_engine.workflow.agents.arbiter import arbiter_node

    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("arbiter", arbiter_node)

    # Entry point
    graph.set_entry_point("planner")

    # Edges
    graph.add_edge("planner", "writer")
    graph.add_edge("writer", "reviewer")

    def route_after_review(state: WorkflowState) -> str:
        if state.conflict_list:
            return "arbiter"
        if state.generation_queue:
            return "writer"
        return END

    graph.add_conditional_edges("reviewer", route_after_review)
    graph.add_edge("arbiter", "writer")

    return graph.compile()
