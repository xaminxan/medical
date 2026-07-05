"""Entity extractor — NER for technical parameters."""
from __future__ import annotations

from typing import Any

from loguru import logger


class EntityExtractor:
    """Extract technical parameters from document text using LLM + rules."""

    # Common FDA parameter patterns (regex-based extraction)
    PARAMETER_PATTERNS = {
        "sterilization_method": [
            r"steriliz(?:e|ation|ed)\s+(?:by\s+)?(\w+(?:\s+\w+)?)",
            r"(EO|ethylene oxide|gamma|autoclave|e-beam|UV)\s+steriliz",
        ],
        "shelf_life": [
            r"shelf\s+life[:\s]+(\d+\s*(?:year|month|day)s?)",
            r"expires?\s+(?:after\s+)?(\d+\s*(?:year|month|day)s?)",
            r"validity\s+period[:\s]+(\d+\s*(?:year|month|day)s?)",
        ],
        "material": [
            r"material[:\s]+(\w+(?:\s+\w+)?)",
            r"(?:made|constructed|fabricated)\s+(?:of|from)\s+(\w+(?:\s+\w+)?)",
            r"(SS316L|Ti6Al4V|PEEK|silicone|polycarbonate|polyethylene)",
        ],
        "dimensions": [
            r"(?:dimension|size)[:\s]+([\d\.]+\s*[xX×]\s*[\d\.]+\s*(?:[xX×]\s*[\d\.]+)?\s*\w*)",
            r"(\d+\.?\d*\s*(?:mm|cm|m|inch|in)\s*[xX×]\s*\d+\.?\d*\s*(?:mm|cm|m|inch|in))",
        ],
        "weight": [
            r"weight[:\s]+(\d+\.?\d*\s*(?:g|kg|lb|oz))",
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
    }

    def extract(self, text: str) -> dict[str, Any]:
        """Extract parameters from text using pattern matching.

        Returns:
            Dict of {param_name: {value, confidence, source_context}}.
        """
        import re

        results = {}

        for param_name, patterns in self.PARAMETER_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    # Get surrounding context
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
