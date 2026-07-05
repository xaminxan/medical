"""Global workflow state definition."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    """Global state shared across all workflow agents."""

    workspace_path: str = ""
    doc_tree: dict[str, Any] = Field(default_factory=dict)
    current_node: str = ""
    generation_queue: list[str] = Field(default_factory=list)
    drafts: dict[str, str] = Field(default_factory=dict)
    truth_params: dict[str, Any] = Field(default_factory=dict)
    extracted_params: dict[str, dict[str, Any]] = Field(default_factory=dict)
    conflict_list: list[dict[str, Any]] = Field(default_factory=list)
    resolved_params: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["auto", "interactive"] = "auto"
    status: Literal["idle", "planning", "generating", "verifying", "blocked", "completed"] = "idle"
    error: str | None = None
