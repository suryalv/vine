from __future__ import annotations

"""
Tests for layers/actions/extractor.py
Mocks Gemini API calls to test JSON parsing and validation logic.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.actions.extractor import get_uw_actions
from models.schemas import UWAction


# ─── Helper ──────────────────────────────────────────────────────


def _make_actions_json(actions: list[dict]) -> str:
    return json.dumps(actions)


VALID_ACTIONS = [
    {
        "action": "Review wind/hail sub-limit adequacy",
        "category": "coverage_gap",
        "priority": "high",
        "details": "Wind/hail sub-limit of $500,000 may be insufficient for coastal exposure.",
        "source_reference": "Endorsement_Package.docx, p2",
    },
    {
        "action": "Verify loss ratio trend",
        "category": "risk_flag",
        "priority": "medium",
        "details": "35% loss ratio is favorable but trending upward.",
        "source_reference": "Loss_Run_Report.pdf, p3",
    },
]

SAMPLE_QUERY = "What are the key risks in this policy?"
SAMPLE_ANSWER = "The policy has a wind/hail sub-limit that may be insufficient."
SAMPLE_CHUNKS = [
    {"text": "Wind endorsement applies.", "source": "endorsement.docx", "page": 2},
    {"text": "Loss ratio is 35%.", "source": "loss_run.pdf", "page": 3},
]


# ─── get_uw_actions with valid JSON ──────────────────────────────


class TestGetUwActionsValid:
    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_returns_list_of_uw_actions(self, mock_extract):
        mock_extract.return_value = _make_actions_json(VALID_ACTIONS)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert isinstance(actions, list)
        assert len(actions) == 2
        assert all(isinstance(a, UWAction) for a in actions)

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_action_fields_populated(self, mock_extract):
        mock_extract.return_value = _make_actions_json(VALID_ACTIONS)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        a = actions[0]
        assert a.action == "Review wind/hail sub-limit adequacy"
        assert a.category == "coverage_gap"
        assert a.priority == "high"
        assert "insufficient" in a.details
        assert a.source_reference == "Endorsement_Package.docx, p2"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_empty_actions_array(self, mock_extract):
        mock_extract.return_value = "[]"
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions == []


# ─── Markdown fence stripping ────────────────────────────────────


class TestMarkdownFenceStripping:
    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_strips_triple_backtick_fences(self, mock_extract):
        raw = "```json\n" + _make_actions_json(VALID_ACTIONS) + "\n```"
        mock_extract.return_value = raw
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert len(actions) == 2

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_strips_plain_backtick_fences(self, mock_extract):
        raw = "```\n" + _make_actions_json(VALID_ACTIONS) + "\n```"
        mock_extract.return_value = raw
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert len(actions) == 2

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_handles_leading_whitespace(self, mock_extract):
        raw = "  \n  " + _make_actions_json(VALID_ACTIONS) + "  \n  "
        mock_extract.return_value = raw
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert len(actions) == 2


# ─── Category and priority validation ────────────────────────────


class TestCategoryPriorityValidation:
    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_invalid_category_defaults_to_risk_flag(self, mock_extract):
        actions_data = [
            {
                "action": "Check something",
                "category": "invalid_category",
                "priority": "high",
                "details": "Detail",
                "source_reference": "ref",
            }
        ]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].category == "risk_flag"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_invalid_priority_defaults_to_medium(self, mock_extract):
        actions_data = [
            {
                "action": "Check something",
                "category": "compliance",
                "priority": "ultra_critical",
                "details": "Detail",
                "source_reference": "ref",
            }
        ]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].priority == "medium"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_all_valid_categories_accepted(self, mock_extract):
        valid_cats = ["coverage_gap", "risk_flag", "endorsement", "compliance", "pricing"]
        actions_data = [
            {"action": f"Action {cat}", "category": cat, "priority": "low", "details": "d", "source_reference": "r"}
            for cat in valid_cats
        ]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert len(actions) == 5
        categories = [a.category for a in actions]
        assert set(categories) == set(valid_cats)

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_all_valid_priorities_accepted(self, mock_extract):
        valid_pris = ["critical", "high", "medium", "low"]
        actions_data = [
            {"action": f"Action {p}", "category": "risk_flag", "priority": p, "details": "d", "source_reference": "r"}
            for p in valid_pris
        ]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        priorities = [a.priority for a in actions]
        assert set(priorities) == set(valid_pris)


# ─── Missing fields and defaults ─────────────────────────────────


class TestMissingFieldDefaults:
    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_missing_action_defaults(self, mock_extract):
        actions_data = [{"category": "risk_flag", "priority": "high", "details": "d", "source_reference": "r"}]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].action == "Review required"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_missing_category_defaults(self, mock_extract):
        actions_data = [{"action": "Do something", "priority": "high", "details": "d", "source_reference": "r"}]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].category == "risk_flag"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_missing_priority_defaults(self, mock_extract):
        actions_data = [{"action": "Do something", "category": "compliance", "details": "d", "source_reference": "r"}]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].priority == "medium"

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_missing_details_defaults_to_empty(self, mock_extract):
        actions_data = [{"action": "Act", "category": "pricing", "priority": "low", "source_reference": "r"}]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].details == ""

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_missing_source_reference_defaults_to_empty(self, mock_extract):
        actions_data = [{"action": "Act", "category": "pricing", "priority": "low", "details": "d"}]
        mock_extract.return_value = _make_actions_json(actions_data)
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions[0].source_reference == ""


# ─── Error handling ──────────────────────────────────────────────


class TestErrorHandling:
    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_invalid_json_returns_empty(self, mock_extract):
        mock_extract.return_value = "This is not JSON at all"
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions == []

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_json_object_instead_of_array_returns_empty(self, mock_extract):
        mock_extract.return_value = '{"action": "single action"}'
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions == []

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_type_error_in_extract_returns_empty(self, mock_extract):
        # The function catches json.JSONDecodeError, KeyError, TypeError
        mock_extract.side_effect = TypeError("type error")
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert actions == []

    @patch("layers.actions.extractor.extract_actions_prompt")
    def test_malformed_items_handled(self, mock_extract):
        # Empty dicts use defaults; None items cause TypeError which is caught
        mock_extract.return_value = json.dumps([
            {"action": "Valid action", "category": "risk_flag", "priority": "high",
             "details": "detail", "source_reference": "ref"},
            {},  # Empty dict — all fields will use defaults
        ])
        actions = get_uw_actions(SAMPLE_QUERY, SAMPLE_ANSWER, SAMPLE_CHUNKS)
        assert isinstance(actions, list)
        assert len(actions) == 2
        assert actions[1].action == "Review required"
