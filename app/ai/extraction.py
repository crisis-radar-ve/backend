"""
Placeholder for the LLM extraction pipeline.

Expected input: raw_text + optional image context.
Expected output: structured dict matching schemas.ReportCreate.
"""

from typing import Any


async def extract_report(raw_text: str, image_text: str | None = None) -> dict[str, Any]:
    # TODO: wire OpenAI / local model with function calling.
    return {
        "category": "HELP_REQUESTED",
        "summary": raw_text[:200],
        "public_summary": raw_text[:120],
        "location_text": None,
        "location_country": "VE",
        "urgency": "medium",
        "confidence": 0.5,
        "language": "es",
        "people": [],
        "organizations": [],
        "contains_sensitive_information": False,
    }
