from __future__ import annotations

"""
ACTIONS LAYER
=============
Extracts structured underwriting actions from AI analysis.
Uses Gemini to identify actionable items, then parses into UWAction objects.

Team Owner: Underwriting Workflow Team
"""

import json
from models.schemas import UWAction
from layers.generation import extract_actions_prompt


def get_uw_actions(
    query: str, answer: str, source_chunks: list[dict]
) -> list[UWAction]:
    """Extract structured underwriting actions from the AI analysis."""
    try:
        raw = extract_actions_prompt(query, answer, source_chunks)

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
