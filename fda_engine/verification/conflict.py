"""Conflict detection and reporting."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Conflict(BaseModel):
    """A single parameter conflict."""

    param_name: str
    source_value: str
    draft_value: str
    comparison_type: str  # vertical | horizontal
    other_doc: str | None = None
    context: str = ""
    suggestion: str = ""


class ConflictReport(BaseModel):
    """Structured conflict report output."""

    doc_id: str
    total_conflicts: int
    conflicts: list[Conflict]
    status: str  # passed | conflict

    @classmethod
    def from_raw(cls, doc_id: str, raw_conflicts: list[dict[str, Any]]) -> "ConflictReport":
        """Build report from raw conflict dicts."""
        conflicts = [Conflict(**c) for c in raw_conflicts if "param_name" in c]
        return cls(
            doc_id=doc_id,
            total_conflicts=len(conflicts),
            conflicts=conflicts,
            status="conflict" if conflicts else "passed",
        )


class ConflictDetector:
    """Detect and report parameter conflicts."""

    def __init__(self, max_before_block: int = 10):
        self.max_before_block = max_before_block

    def should_block(self, conflicts: list[dict[str, Any]]) -> bool:
        """Check if generation should be blocked due to too many conflicts."""
        return len(conflicts) >= self.max_before_block

    def generate_report(
        self,
        doc_id: str,
        conflicts: list[dict[str, Any]],
    ) -> ConflictReport:
        """Generate a structured conflict report."""
        return ConflictReport.from_raw(doc_id, conflicts)
