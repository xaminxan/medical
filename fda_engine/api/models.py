"""Pydantic models for FDA Engine API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorkspaceInitRequest(BaseModel):
    """Request to initialize a workspace from a folder of tech documents."""

    folder_path: str = Field(..., description="Path to folder containing product technical documents")
    fda_template: str = Field(
        default="510k",
        description="Template: '510k', 'nmpa', 'qtms_fda', 'qtms_nmpa'"
    )


class WorkspaceInitResponse(BaseModel):
    """Response after workspace initialization."""

    workspace_id: str
    workspace_path: str = ""
    documents_indexed: int
    parameters_extracted: dict[str, Any]
    product_characteristics: dict[str, Any] = {}
    status: str
    language: str = "en"  # en or zh


class DocumentTreeNode(BaseModel):
    """A node in the FDA document tree."""

    node_id: str
    title: str
    required: bool = True
    description: str = ""
    children: list[DocumentTreeNode] = Field(default_factory=list)
    status: str = "pending"  # pending | generating | generated | verified | conflict


class DocumentTreeResponse(BaseModel):
    """Response containing the full FDA document tree."""

    template: str
    root: DocumentTreeNode


class DocumentGenerateRequest(BaseModel):
    """Request to generate documents."""

    node_id: str = Field(default="all", description="Node ID to generate, or 'all' for full generation")
    mode: str = Field(default="auto", description="Generation mode: 'auto' or 'interactive'")


class DocumentGenerateResponse(BaseModel):
    """Response after triggering generation."""

    task_id: str
    status: str
    message: str


class VerifyGlobalRequest(BaseModel):
    """Request to trigger global consistency verification."""

    document_ids: list[str] | None = Field(
        default=None,
        description="Specific document IDs to verify, or None for all",
    )


class ConflictItem(BaseModel):
    """A single conflict item."""

    param_name: str
    source_value: str
    draft_value: str
    comparison_type: str  # vertical | horizontal
    other_doc: str | None = None
    context: str = ""
    suggestion: str = ""


class VerifyGlobalResponse(BaseModel):
    """Response containing verification results."""

    total_conflicts: int
    conflicts: list[ConflictItem]
    status: str  # passed | conflict


class VerifyResolveRequest(BaseModel):
    """Request to resolve a conflict (human-in-the-loop)."""

    param_name: str = Field(..., description="Parameter name to resolve")
    resolved_value: str = Field(..., description="The human-decided correct value")
    apply_to_all: bool = Field(default=True, description="Cascade update to all documents")


class VerifyResolveResponse(BaseModel):
    """Response after conflict resolution."""

    param_name: str
    resolved_value: str
    documents_updated: int
    status: str


class WsProgressEvent(BaseModel):
    """WebSocket progress event."""

    event: str  # started | progress | completed | error
    task_id: str | None = None
    node_id: str | None = None
    progress: float | None = None  # 0.0 - 1.0
    message: str = ""
    data: dict[str, Any] | None = None
