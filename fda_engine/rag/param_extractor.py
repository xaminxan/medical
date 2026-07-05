"""Parameter extractor — extract key-value parameter matrices from documents."""
from __future__ import annotations

from typing import Any

from loguru import logger


class ParameterExtractor:
    """Extract structured parameter matrices from document text.

    Uses a combination of regex patterns and LLM extraction
    to identify technical parameters like sterilization method,
    shelf life, materials, dimensions, etc.
    """

    # Key parameter patterns for FDA medical devices
    PARAMETER_PATTERNS = {
        "sterilization_method": [
            r"steriliz(?:e|ation|ed)\s+(?:by\s+)?(EO|ethylene oxide|gamma|autoclave|e-beam|UV|dry heat|plasma|nitrogen dioxide)",
        ],
        "shelf_life": [
            r"shelf\s+life[:\s]+(\d+\s*(?:year|month|day)s?)",
            r"expires?\s+(?:after\s+)?(\d+\s*(?:year|month|day)s?)",
        ],
        "material": [
            r"(SS316L|Ti6Al4V|PEEK|silicone|polycarbonate|polyethylene|polypropylene|ABS|PMMA|titanium|stainless steel)",
        ],
        "biocompatibility": [
            r"(?:biocompatib(?:le|ility))[:\s]+(ISO\s+10993[-\s]?\d*)",
        ],
        "electrical_safety": [
            r"(IEC\s+60601[-\s]?\d*)",
        ],
        "intended_use": [
            r"intended\s+use[:\s]+(.+?)(?:\.|$)",
        ],
        "regulatory_class": [
            r"(?:class|classification)[:\s]+(I{1,3}V?|II|III)",
        ],
        "product_code": [
            r"product\s+code[:\s]+([A-Z]{1,3}\d{4})",
        ],
        "regulation_number": [
            r"(?:regulation|21\s*CFR)\s*(?:number|#)?[:\s]+(\d+\.\d+)",
        ],
    }

    def extract(self, text: str) -> dict[str, Any]:
        """Extract parameters from text using pattern matching.

        Returns:
            Dict of {param_name: {value, confidence, source_context}}.
        """
        results = {}

        for param_name, patterns in self.PARAMETER_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()

                    results[param_name] = {
                        "value": value.strip(),
                        "confidence": 0.8,
                        "source_context": context,
                    }
                    break

        logger.debug(f"Extracted {len(results)} parameters")
        return results

    def extract_all_documents(self, documents: dict[str, str]) -> dict[str, dict[str, Any]]:
        """Extract parameters from multiple documents.

        Returns:
            Dict of {doc_id: {param_name: {value, confidence, source_context}}}.
        """
        return {
            doc_id: self.extract(content)
            for doc_id, content in documents.items()
        }


import re  # noqa: E402
