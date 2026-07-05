"""Central supervisor for workflow routing decisions."""
from __future__ import annotations

from loguru import logger

from fda_engine.workflow.state import WorkflowState


class WorkflowSupervisor:
    """Central coordinator that decides the next action based on workflow state."""

    def __init__(self, state: WorkflowState):
        self.state = state

    def decide_next(self) -> str:
        """Determine the next agent to activate.

        Returns:
            Agent name: "planner", "writer", "reviewer", "arbiter", or "done".
        """
        if self.state.status == "idle":
            return "planner"

        if self.state.status == "planning":
            return "writer" if self.state.generation_queue else "done"

        if self.state.status == "generating":
            return "reviewer" if self.state.current_node else "done"

        if self.state.status == "verifying":
            if self.state.conflict_list:
                return "arbiter"
            if self.state.generation_queue:
                return "writer"
            return "done"

        if self.state.status == "blocked":
            logger.info("Workflow blocked — waiting for human resolution")
            return "done"

        if self.state.status == "completed":
            return "done"

        return "done"

    def should_continue(self) -> bool:
        """Check if the workflow should continue."""
        return self.decide_next() != "done"
