"""
Facade for the AI extraction pipeline.
"""

from typing import Any

from app.services.extraction import extract_report as _extract_report


def extract_report(raw_text: str, image_text: str | None = None) -> dict[str, Any]:
    """Extract structured report from raw text."""
    return _extract_report(raw_text, image_text)
