"""FDA regulatory gap analysis — compare QMS documents against regulatory requirements."""
from __future__ import annotations

from typing import Any

from loguru import logger


class GapAnalyzer:
    """Analyze gaps between QMS documents and FDA regulatory requirements."""

    # Common FDA 510(k) requirements (simplified)
    REQUIREMENTS = {
        "design_controls": {
            "title": "Design Controls (21 CFR 820.30)",
            "description": "Design input, output, review, verification, validation, and transfer",
            "keywords": ["design input", "design output", "design review", "design verification", "design validation"],
        },
        "risk_management": {
            "title": "Risk Management (ISO 14971)",
            "description": "Risk analysis, evaluation, and control",
            "keywords": ["risk analysis", "risk evaluation", "risk control", "risk assessment"],
        },
        "document_controls": {
            "title": "Document Controls (21 CFR 820.40)",
            "description": "Document approval, distribution, change control",
            "keywords": ["document control", "change control", "approval process"],
        },
        "purchasing_controls": {
            "title": "Purchasing Controls (21 CFR 820.50)",
            "description": "Supplier evaluation, purchasing data",
            "keywords": ["supplier evaluation", "purchasing", "supplier qualification"],
        },
        "production_controls": {
            "title": "Production & Process Controls (21 CFR 820.70)",
            "description": "Process validation, environmental controls",
            "keywords": ["process validation", "production process", "environmental control"],
        },
        "corrective_preventive": {
            "title": "CAPA (21 CFR 820.90)",
            "description": "Corrective and preventive action",
            "keywords": ["corrective action", "preventive action", "CAPA", "nonconformance"],
        },
        "complaint_handling": {
            "title": "Complaint Handling (21 CFR 820.198)",
            "description": "Complaint evaluation and investigation",
            "keywords": ["complaint", "complaint handling", "investigation"],
        },
        "labeling_controls": {
            "title": "Labeling Controls (21 CFR 820.120)",
            "description": "Labeling storage, distribution, and control",
            "keywords": ["labeling", "label control", "IFU", "instructions for use"],
        },
        "biocompatibility": {
            "title": "Biocompatibility (ISO 10993)",
            "description": "Biocompatibility evaluation for body-contact devices",
            "keywords": ["biocompatibility", "ISO 10993", "biological evaluation"],
        },
        "sterilization": {
            "title": "Sterilization Validation",
            "description": "Sterilization process validation",
            "keywords": ["sterilization", "sterility", "validation", "EO", "gamma"],
        },
    }

    def __init__(self):
        self._requirements = dict(self.REQUIREMENTS)

    def analyze_gaps(
        self,
        qms_documents: dict[str, str],
    ) -> dict[str, Any]:
        """Analyze gaps between QMS documents and regulatory requirements.

        Args:
            qms_documents: Dict of {doc_id: content} for all QMS documents.

        Returns:
            Gap analysis report.
        """
        covered = []
        partial = []
        missing = []

        all_content = " ".join(qms_documents.values()).lower()

        for req_id, req_info in self._requirements.items():
            coverage = self._check_requirement_coverage(req_id, req_info, all_content)

            if coverage >= 0.8:
                covered.append({
                    "requirement_id": req_id,
                    "title": req_info["title"],
                    "coverage": coverage,
                })
            elif coverage >= 0.3:
                partial.append({
                    "requirement_id": req_id,
                    "title": req_info["title"],
                    "coverage": coverage,
                    "keywords_found": self._find_matching_keywords(req_info["keywords"], all_content),
                })
            else:
                missing.append({
                    "requirement_id": req_id,
                    "title": req_info["title"],
                    "description": req_info["description"],
                    "suggested_keywords": req_info["keywords"],
                })

        return {
            "total_requirements": len(self._requirements),
            "covered": len(covered),
            "partial": len(partial),
            "missing": len(missing),
            "coverage_score": len(covered) / len(self._requirements) if self._requirements else 0,
            "covered_items": covered,
            "partial_items": partial,
            "missing_items": missing,
        }

    def _check_requirement_coverage(
        self,
        req_id: str,
        req_info: dict,
        all_content: str,
    ) -> float:
        """Check how well a requirement is covered by QMS documents."""
        keywords = req_info.get("keywords", [])
        if not keywords:
            return 0.0

        found = sum(1 for kw in keywords if kw.lower() in all_content)
        return found / len(keywords)

    def _find_matching_keywords(
        self,
        keywords: list[str],
        content: str,
    ) -> list[str]:
        """Find which keywords are present in the content."""
        return [kw for kw in keywords if kw.lower() in content]

    def generate_report(
        self,
        qms_documents: dict[str, str],
    ) -> str:
        """Generate a human-readable gap analysis report."""
        analysis = self.analyze_gaps(qms_documents)

        lines = [
            "=" * 60,
            "FDA Regulatory Gap Analysis Report",
            "=" * 60,
            f"Total Requirements: {analysis['total_requirements']}",
            f"Covered: {analysis['covered']}",
            f"Partial: {analysis['partial']}",
            f"Missing: {analysis['missing']}",
            f"Coverage Score: {analysis['coverage_score']:.1%}",
            "",
        ]

        if analysis["missing_items"]:
            lines.append("MISSING REQUIREMENTS:")
            lines.append("-" * 40)
            for item in analysis["missing_items"]:
                lines.append(f"  - {item['title']}")
                lines.append(f"    {item['description']}")
                lines.append(f"    Suggested: {', '.join(item['suggested_keywords'][:3])}")
                lines.append("")

        if analysis["partial_items"]:
            lines.append("PARTIAL COVERAGE:")
            lines.append("-" * 40)
            for item in analysis["partial_items"]:
                lines.append(f"  - {item['title']} ({item['coverage']:.0%})")
                lines.append(f"    Found: {', '.join(item['keywords_found'][:3])}")
                lines.append("")

        if analysis["covered_items"]:
            lines.append("COVERED REQUIREMENTS:")
            lines.append("-" * 40)
            for item in analysis["covered_items"]:
                lines.append(f"  - {item['title']} ({item['coverage']:.0%})")

        return "\n".join(lines)
