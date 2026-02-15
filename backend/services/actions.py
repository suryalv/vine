from __future__ import annotations

"""
Underwriting actions extraction service.
Uses Gemini to identify actionable items from document analysis,
then parses them into structured UWAction objects.
"""

import json
from models.schemas import UWAction
from services.gemini_service import extract_actions


def get_uw_actions(
    query: str, answer: str, source_chunks: list[dict]
) -> list[UWAction]:
    """
    Extract structured underwriting actions from the AI analysis.

    Returns:
        List of UWAction objects with category, priority, and source references
    """
    try:
        raw = extract_actions(query, answer, source_chunks)

        # Clean up potential markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        actions_data = json.loads(raw)

        if not isinstance(actions_data, list):
            return []

        actions = []
        valid_categories = {"coverage_gap", "risk_flag", "endorsement", "compliance", "pricing"}
        valid_priorities = {"critical", "high", "medium", "low"}

        for item in actions_data:
            category = item.get("category", "risk_flag")
            if category not in valid_categories:
                category = "risk_flag"

            priority = item.get("priority", "medium")
            if priority not in valid_priorities:
                priority = "medium"

            actions.append(
                UWAction(
                    action=item.get("action", "Review required"),
                    category=category,
                    priority=priority,
                    details=item.get("details", ""),
                    source_reference=item.get("source_reference", ""),
                )
            )

        return actions

    except (json.JSONDecodeError, KeyError, TypeError):
        return []
