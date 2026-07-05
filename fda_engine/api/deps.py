"""Dependency injection for FDA Engine API."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fda_engine.core.config import FDAConfig
from fda_engine.core.engine import FDAEngine


class EngineState:
    """Shared state for the FDA engine instance."""

    def __init__(self):
        self.config = FDAConfig()
        self.engine = FDAEngine(self.config)
        self.workspace_path: Path | None = None
        self.truth_params: dict[str, Any] = {}
        self.product_characteristics: dict[str, Any] = {}
        self.document_tree: dict[str, Any] = {}
        self.generated_docs: dict[str, str] = {}  # node_id -> content
        self.extracted_params: dict[str, dict[str, Any]] = {}  # node_id -> params
        self.active_tasks: dict[str, asyncio.Task] = {}
        self.ws_clients: set = set()
        # Generation progress tracking
        self.generation_status: str = "idle"  # idle | generating | completed | error
        self.generation_progress: dict[str, Any] = {
            "current": 0,
            "total": 0,
            "current_node": "",
            "completed_nodes": [],
            "message": ""
        }


_state: EngineState | None = None


def get_state() -> EngineState:
    """Get or create the global engine state."""
    global _state
    if _state is None:
        _state = EngineState()
    return _state


async def get_engine() -> FDAEngine:
    """Get the initialized FDA engine."""
    state = get_state()
    if not state.engine._initialized:
        await state.engine.initialize()
    return state.engine
