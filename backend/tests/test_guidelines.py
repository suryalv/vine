from __future__ import annotations

"""
Tests for layers/guidelines/
Verifies guidelines store, enforcement engine, and API endpoints.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import GuidelineViolation, EnforcementReport


# ─── Guidelines Store Tests ───────────────────────────────────────


class TestGuidelinesStore:
    """Tests for the GuidelinesStore class."""

    def test_store_import(self):
        """GuidelinesStore can be imported."""
        from layers.guidelines.guidelines_store import GuidelinesStore
        assert GuidelinesStore is not None

    def test_singleton_factory(self):
        """get_guidelines_store returns a singleton."""
        from layers.guidelines.guidelines_store import (
            get_guidelines_store,
            reset_guidelines_store,
        )
        reset_guidelines_store()
        store1 = get_guidelines_store()
        store2 = get_guidelines_store()
        assert store1 is store2
        reset_guidelines_store()

    def test_reset_clears_singleton(self):
        """reset_guidelines_store clears the singleton."""
        from layers.guidelines.guidelines_store import (
            get_guidelines_store,
            reset_guidelines_store,
        )
        reset_guidelines_store()
        store1 = get_guidelines_store()
        reset_guidelines_store()
        store2 = get_guidelines_store()
        assert store1 is not store2
        reset_guidelines_store()

    def test_store_has_required_methods(self):
        """GuidelinesStore has all required methods."""
        from layers.guidelines.guidelines_store import GuidelinesStore
        required = {
            "store_guideline_chunks",
            "search_guidelines",
            "search_by_line",
            "list_guidelines",
            "delete_guideline",
        }
        methods = {m for m in dir(GuidelinesStore) if not m.startswith("_")}
        assert required.issubset(methods)

    def test_list_guidelines_empty(self):
        """list_guidelines returns empty list when no guidelines stored."""
        from layers.guidelines.guidelines_store import GuidelinesStore
        store = GuidelinesStore(db_path="/tmp/test_guidelines_empty", table_name="test_gl_empty")
        result = store.list_guidelines()
        assert result == []

    def test_search_guidelines_empty(self):
        """search_guidelines returns empty list when no table exists."""
        from layers.guidelines.guidelines_store import GuidelinesStore
        store = GuidelinesStore(db_path="/tmp/test_guidelines_empty", table_name="test_gl_empty")
        result = store.search_guidelines("test query")
        assert result == []


# ─── Enforcer Tests ───────────────────────────────────────────────


class TestEnforcer:
    """Tests for the enforcement engine."""

    def test_enforcer_import(self):
        """enforce_guidelines can be imported."""
        from layers.guidelines.enforcer import enforce_guidelines
        assert enforce_guidelines is not None

    @patch("layers.guidelines.enforcer.get_chunks_by_document")
    @patch("layers.guidelines.enforcer.get_all_documents")
    @patch("layers.guidelines.enforcer.get_guidelines_store")
    @patch("layers.guidelines.enforcer.get_llm_provider")
    def test_enforce_returns_report(self, mock_llm, mock_store, mock_docs, mock_chunks):
        """enforce_guidelines returns an EnforcementReport."""
        from layers.guidelines.enforcer import enforce_guidelines

        mock_chunks.return_value = [
            {"text": "Commercial property policy for Acme Corp", "source": "policy.pdf", "page": 1}
        ]
        mock_docs.return_value = [
            {"document_id": "doc-1", "filename": "policy.pdf", "num_chunks": 1, "num_pages": 1}
        ]

        mock_store_instance = MagicMock()
        mock_store_instance.search_by_line.return_value = [
            {
                "text": "Rule P-101: Minimum building limit is $1M",
                "source": "Property_Guidelines.docx",
                "page": 1,
                "section": "SECTION 2",
                "similarity": 0.85,
                "guideline_id": "gl-1",
                "line_of_business": "property",
            }
        ]
        mock_store.return_value = mock_store_instance

        llm_response = json.dumps({
            "findings": [
                {
                    "rule": "Minimum building limit is $1M",
                    "status": "compliant",
                    "finding": "Building limit is $42.5M",
                    "guideline_reference": "Property_Guidelines.docx, Section 2",
                    "recommendation": "No action needed",
                }
            ],
            "summary": "Policy is compliant with guidelines.",
        })
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_simple.return_value = llm_response
        mock_llm.return_value = mock_llm_instance

        report = enforce_guidelines("doc-1", "property")
        assert isinstance(report, EnforcementReport)
        assert report.document_id == "doc-1"
        assert report.num_compliant == 1
        assert report.num_violations == 0
        assert report.compliance_score == 100.0

    @patch("layers.guidelines.enforcer.get_chunks_by_document")
    @patch("layers.guidelines.enforcer.get_all_documents")
    @patch("layers.guidelines.enforcer.get_guidelines_store")
    @patch("layers.guidelines.enforcer.get_llm_provider")
    def test_enforce_with_violations(self, mock_llm, mock_store, mock_docs, mock_chunks):
        """enforce_guidelines correctly counts violations."""
        from layers.guidelines.enforcer import enforce_guidelines

        mock_chunks.return_value = [
            {"text": "EMR is 1.55, TRIR is 8.4", "source": "submission.pdf", "page": 1}
        ]
        mock_docs.return_value = [
            {"document_id": "doc-2", "filename": "submission.pdf", "num_chunks": 1, "num_pages": 1}
        ]

        mock_store_instance = MagicMock()
        mock_store_instance.search_guidelines.return_value = [
            {
                "text": "Rule WC-201: Decline if EMR > 1.50",
                "source": "WC_Guidelines.docx",
                "page": 2,
                "section": "SECTION 2",
                "similarity": 0.9,
                "guideline_id": "gl-2",
                "line_of_business": "workers_comp",
            }
        ]
        mock_store.return_value = mock_store_instance

        llm_response = json.dumps({
            "findings": [
                {
                    "rule": "Decline if EMR > 1.50",
                    "status": "violation",
                    "finding": "EMR is 1.55, exceeds 1.50 threshold",
                    "guideline_reference": "WC_Guidelines.docx, Section 2",
                    "recommendation": "Decline the submission or request loss control review",
                },
                {
                    "rule": "TRIR must be below 2x industry average",
                    "status": "warning",
                    "finding": "TRIR is 8.4, industry average not available for comparison",
                    "guideline_reference": "WC_Guidelines.docx, Section 4",
                    "recommendation": "Request industry TRIR data to complete evaluation",
                },
            ],
            "summary": "Submission has critical EMR violation.",
        })
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_simple.return_value = llm_response
        mock_llm.return_value = mock_llm_instance

        report = enforce_guidelines("doc-2")
        assert report.num_violations == 1
        assert report.num_warnings == 1
        assert report.num_compliant == 0
        assert report.compliance_score == 25.0  # (0 + 0.5*1) / 2 * 100 = 25
        assert len(report.violations) == 2

    @patch("layers.guidelines.enforcer.get_chunks_by_document")
    def test_enforce_no_chunks_raises(self, mock_chunks):
        """enforce_guidelines raises ValueError when document not found."""
        from layers.guidelines.enforcer import enforce_guidelines

        mock_chunks.return_value = []
        with pytest.raises(ValueError, match="No chunks found"):
            enforce_guidelines("nonexistent-doc")

    @patch("layers.guidelines.enforcer.get_chunks_by_document")
    @patch("layers.guidelines.enforcer.get_all_documents")
    @patch("layers.guidelines.enforcer.get_guidelines_store")
    def test_enforce_no_guidelines(self, mock_store, mock_docs, mock_chunks):
        """enforce_guidelines returns empty report when no guidelines loaded."""
        from layers.guidelines.enforcer import enforce_guidelines

        mock_chunks.return_value = [
            {"text": "Some submission text", "source": "sub.pdf", "page": 1}
        ]
        mock_docs.return_value = [
            {"document_id": "doc-3", "filename": "sub.pdf", "num_chunks": 1, "num_pages": 1}
        ]

        mock_store_instance = MagicMock()
        mock_store_instance.search_guidelines.return_value = []
        mock_store.return_value = mock_store_instance

        report = enforce_guidelines("doc-3")
        assert report.num_guidelines_checked == 0
        assert report.compliance_score == 100.0
        assert "No underwriting guidelines" in report.summary

    @patch("layers.guidelines.enforcer.get_chunks_by_document")
    @patch("layers.guidelines.enforcer.get_all_documents")
    @patch("layers.guidelines.enforcer.get_guidelines_store")
    @patch("layers.guidelines.enforcer.get_llm_provider")
    def test_enforce_llm_parse_error(self, mock_llm, mock_store, mock_docs, mock_chunks):
        """enforce_guidelines handles LLM returning invalid JSON."""
        from layers.guidelines.enforcer import enforce_guidelines

        mock_chunks.return_value = [
            {"text": "Some text", "source": "doc.pdf", "page": 1}
        ]
        mock_docs.return_value = [
            {"document_id": "doc-4", "filename": "doc.pdf", "num_chunks": 1, "num_pages": 1}
        ]

        mock_store_instance = MagicMock()
        mock_store_instance.search_guidelines.return_value = [
            {"text": "Rule", "source": "gl.docx", "page": 1, "section": "",
             "similarity": 0.8, "guideline_id": "gl-1", "line_of_business": "property"}
        ]
        mock_store.return_value = mock_store_instance

        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_simple.return_value = "This is not valid JSON"
        mock_llm.return_value = mock_llm_instance

        report = enforce_guidelines("doc-4")
        assert report.compliance_score == 50.0
        assert "Could not parse" in report.summary


# ─── Schema Tests ─────────────────────────────────────────────────


class TestGuidelineSchemas:
    """Tests for guideline-related Pydantic models."""

    def test_guideline_violation_model(self):
        v = GuidelineViolation(
            rule="Min limit $1M",
            status="violation",
            finding="Limit is $500K",
            guideline_reference="Property_GL.docx, p1",
            recommendation="Increase limit",
        )
        assert v.status == "violation"
        assert v.rule == "Min limit $1M"

    def test_enforcement_report_model(self):
        report = EnforcementReport(
            document_id="doc-1",
            document_name="test.pdf",
            line_of_business="property",
            num_guidelines_checked=5,
            num_violations=1,
            num_warnings=2,
            num_compliant=3,
            compliance_score=72.5,
            violations=[],
            summary="Test summary",
        )
        assert report.compliance_score == 72.5
        assert report.line_of_business == "property"

    def test_enforcement_report_score_bounds(self):
        """compliance_score must be 0-100."""
        with pytest.raises(Exception):
            EnforcementReport(
                document_id="x",
                document_name="x",
                line_of_business="x",
                num_guidelines_checked=0,
                num_violations=0,
                num_warnings=0,
                num_compliant=0,
                compliance_score=150.0,  # Invalid
                violations=[],
                summary="",
            )


# ─── Public API Tests ─────────────────────────────────────────────


class TestGuidelinesPublicAPI:
    """Tests for layers/guidelines/__init__.py public API."""

    def test_public_api_exports(self):
        """All public functions are importable."""
        from layers.guidelines import (
            store_guideline_chunks,
            search_guidelines,
            search_guidelines_by_line,
            list_guidelines,
            delete_guideline,
            enforce_guidelines,
        )
        assert callable(store_guideline_chunks)
        assert callable(search_guidelines)
        assert callable(search_guidelines_by_line)
        assert callable(list_guidelines)
        assert callable(delete_guideline)
        assert callable(enforce_guidelines)

    @patch("layers.guidelines.get_guidelines_store")
    def test_list_guidelines_delegates(self, mock_store):
        """list_guidelines delegates to store."""
        from layers.guidelines import list_guidelines

        mock_instance = MagicMock()
        mock_instance.list_guidelines.return_value = [{"guideline_id": "gl-1"}]
        mock_store.return_value = mock_instance

        result = list_guidelines()
        assert result == [{"guideline_id": "gl-1"}]
        mock_instance.list_guidelines.assert_called_once()

    @patch("layers.guidelines.get_guidelines_store")
    def test_delete_guideline_delegates(self, mock_store):
        """delete_guideline delegates to store."""
        from layers.guidelines import delete_guideline

        mock_instance = MagicMock()
        mock_instance.delete_guideline.return_value = True
        mock_store.return_value = mock_instance

        result = delete_guideline("gl-1")
        assert result is True
        mock_instance.delete_guideline.assert_called_once_with("gl-1")


# ─── RAG Generator Integration Tests ─────────────────────────────


class TestRAGGeneratorGuidelines:
    """Tests for guidelines integration in rag_generator."""

    @patch("layers.generation.rag_generator.get_llm_provider")
    def test_generate_with_guidelines(self, mock_llm):
        """generate_rag_response accepts guideline_chunks parameter."""
        from layers.generation.rag_generator import generate_rag_response

        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Test response"
        mock_llm.return_value = mock_instance

        result = generate_rag_response(
            query="What is the limit?",
            context_chunks=[{"text": "Limit is $1M", "source": "policy.pdf", "page": 1}],
            guideline_chunks=[{"text": "Min limit $500K", "source": "guidelines.docx", "page": 1}],
        )
        assert result == "Test response"

        # Verify the user prompt includes guidelines context
        call_args = mock_instance.generate.call_args
        user_prompt = call_args.kwargs.get("user_prompt", "") or call_args[1].get("user_prompt", "")
        if not user_prompt:
            user_prompt = call_args[0][0] if call_args[0] else ""
        assert "UNDERWRITING GUIDELINES" in user_prompt or "Guideline" in user_prompt

    @patch("layers.generation.rag_generator.get_llm_provider")
    def test_generate_without_guidelines(self, mock_llm):
        """generate_rag_response works without guidelines (backward compat)."""
        from layers.generation.rag_generator import generate_rag_response

        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Test response"
        mock_llm.return_value = mock_instance

        result = generate_rag_response(
            query="What is the limit?",
            context_chunks=[{"text": "Limit is $1M", "source": "policy.pdf", "page": 1}],
        )
        assert result == "Test response"

        # Verify no guidelines block
        call_args = mock_instance.generate.call_args
        user_prompt = call_args.kwargs.get("user_prompt", "") or call_args[1].get("user_prompt", "")
        if not user_prompt:
            user_prompt = call_args[0][0] if call_args[0] else ""
        assert "UNDERWRITING GUIDELINES" not in user_prompt


# ─── Config Tests ─────────────────────────────────────────────────


class TestGuidelinesConfig:
    """Tests for guidelines config values."""

    def test_config_values_exist(self):
        from config import GUIDELINES_TABLE_NAME, GUIDELINES_TOP_K
        assert GUIDELINES_TABLE_NAME == "uw_guidelines"
        assert GUIDELINES_TOP_K == 15

    def test_config_values_are_correct_types(self):
        from config import GUIDELINES_TABLE_NAME, GUIDELINES_TOP_K
        assert isinstance(GUIDELINES_TABLE_NAME, str)
        assert isinstance(GUIDELINES_TOP_K, int)
