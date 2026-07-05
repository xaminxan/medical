"""FDA document tree definitions for 510(k) and eSTAR."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocNode:
    """A node in the FDA document tree."""

    node_id: str
    title: str
    required: bool = True
    description: str = ""
    children: list[DocNode] = field(default_factory=list)
    generation_prompt: str = ""

    def flatten(self) -> list[DocNode]:
        """Flatten tree into a list."""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.flatten())
        return nodes

    def find(self, node_id: str) -> DocNode | None:
        """Find a node by ID."""
        if self.node_id == node_id:
            return self
        for child in self.children:
            found = child.find(node_id)
            if found:
                return found
        return None


def build_510k_tree() -> DocNode:
    """Build the complete 510(k) document tree."""
    return DocNode(
        node_id="root",
        title="510(k) Submission Package",
        required=True,
        description="Complete FDA 510(k) premarket notification",
        children=[
            DocNode(
                node_id="cover_letter",
                title="Cover Letter",
                required=True,
                description="Submission cover letter",
            ),
            DocNode(
                node_id="510k_summary",
                title="510(k) Summary",
                required=True,
                description="Summary of safety and effectiveness data",
            ),
            DocNode(
                node_id="indication_for_use",
                title="Indications for Use Statement",
                required=True,
                description="FDA Form 3881",
            ),
            DocNode(
                node_id="device_description",
                title="Device Description",
                required=True,
                description="Detailed device description and specifications",
                children=[
                    DocNode(
                        node_id="technical_specs",
                        title="Technical Specifications",
                        required=True,
                        description="Dimensions, materials, weight",
                    ),
                    DocNode(
                        node_id="device_diagrams",
                        title="Device Diagrams",
                        required=True,
                        description="Drawings, photos, illustrations",
                    ),
                ],
            ),
            DocNode(
                node_id="substantial_equivalence",
                title="Substantial Equivalence",
                required=True,
                description="Comparison with predicate device",
                children=[
                    DocNode(
                        node_id="se_comparison",
                        title="Comparison Table",
                        required=True,
                        description="Side-by-side comparison",
                    ),
                    DocNode(
                        node_id="se_analysis",
                        title="Equivalence Analysis",
                        required=True,
                        description="Analysis of substantial equivalence",
                    ),
                ],
            ),
            DocNode(
                node_id="performance_testing",
                title="Performance Testing",
                required=True,
                description="Safety and effectiveness test results",
                children=[
                    DocNode(
                        node_id="biocompatibility_testing",
                        title="Biocompatibility (ISO 10993)",
                        required=True,
                        description="Biocompatibility evaluation",
                    ),
                    DocNode(
                        node_id="electrical_safety_testing",
                        title="Electrical Safety (IEC 60601)",
                        required=False,
                        description="Electrical safety and EMC",
                    ),
                    DocNode(
                        node_id="sterilization_validation",
                        title="Sterilization Validation",
                        required=False,
                        description="Sterilization method validation",
                    ),
                    DocNode(
                        node_id="shelf_life_testing",
                        title="Shelf Life Testing",
                        required=False,
                        description="Aging and packaging studies",
                    ),
                    DocNode(
                        node_id="functional_testing",
                        title="Functional Testing",
                        required=True,
                        description="Device-specific performance testing",
                    ),
                ],
            ),
            DocNode(
                node_id="biocompatibility_report",
                title="Biocompatibility Report",
                required=True,
                description="Comprehensive biocompatibility report",
            ),
            DocNode(
                node_id="software_documentation",
                title="Software Documentation",
                required=False,
                description="Software level of concern",
            ),
            DocNode(
                node_id="cybersecurity",
                title="Cybersecurity Documentation",
                required=False,
                description="Cybersecurity risk management",
            ),
            DocNode(
                node_id="labeling",
                title="Labeling",
                required=True,
                description="Device labeling and IFU",
                children=[
                    DocNode(
                        node_id="ifu",
                        title="Instructions for Use",
                        required=True,
                        description="User instructions",
                    ),
                    DocNode(
                        node_id="device_labels",
                        title="Device Labels",
                        required=True,
                        description="Labels and packaging",
                    ),
                ],
            ),
            DocNode(
                node_id="risk_management",
                title="Risk Management (ISO 14971)",
                required=True,
                description="Risk analysis and control",
            ),
            DocNode(
                node_id="clinical_data",
                title="Clinical Data",
                required=False,
                description="Clinical evidence",
            ),
            DocNode(
                node_id="truth_of_origin",
                title="Truth of Origin Letter",
                required=True,
                description="Right to reference third-party data",
            ),
            DocNode(
                node_id="declarations",
                title="Declarations",
                required=True,
                description="Truthful and accurate statement",
            ),
        ],
    )


FDA_DOC_TREES = {
    "510k": build_510k_tree,
}
