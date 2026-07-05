"""FDA-specific configuration extending the base nanobot config."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from agent_core.config_base import Base


class RAGConfig(Base):
    """RAG engine configuration."""

    vector_db_path: str = Field(default="~/.fda_engine/vector_db")
    chunk_size: int = Field(default=1024, ge=128)
    chunk_overlap: int = Field(default=128, ge=0)
    embedding_model: str = "text-embedding-3-small"
    product_space_name: str = "product_tech_space"
    law_space_name: str = "qms_law_space"


class VerificationConfig(Base):
    """Consistency verification configuration."""

    max_conflicts_before_block: int = Field(default=10, ge=1)
    auto_resolve_threshold: float = Field(
        default=0.9, ge=0.0, le=1.0,
        description="Similarity threshold for auto-resolving minor conflicts",
    )
    cascade_rewrite_batch_size: int = Field(default=5, ge=1)


class WorkflowConfig(Base):
    """Multi-agent workflow configuration."""

    max_iterations_per_node: int = Field(default=50, ge=1)
    parallel_generation: bool = True
    timeout_per_node_seconds: int = Field(default=300, ge=30)


class FDAConfig(Base):
    """Root FDA engine configuration."""

    workspace_path: str = Field(default="~/.fda_engine/workspace")
    fda_template: Literal["510k", "estar", "nmpa", "qtms_fda", "qtms_nmpa"] = "510k"
    language: Literal["en", "zh"] = "en"
    rag: RAGConfig = Field(default_factory=RAGConfig)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)

    @property
    def workspace_dir(self) -> Path:
        return Path(self.workspace_path).expanduser()

    @property
    def vector_db_dir(self) -> Path:
        return Path(self.rag.vector_db_path).expanduser()
