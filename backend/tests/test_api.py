from __future__ import annotations

"""
Tests for main.py FastAPI endpoints using httpx TestClient.
All external services (Gemini, LanceDB embedding) are mocked.
"""

import io
import json
import sys
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app, _chat_history
from models.schemas import HallucinationReport


def _make_hallucination_report(**kwargs):
    """Create a valid HallucinationReport with defaults."""
    defaults = dict(
        overall_score=80.0,
        retrieval_confidence=80.0,
        response_grounding=80.0,
        numerical_fidelity=100.0,
        entity_consistency=100.0,
        sentence_details=[],
        flagged_claims=[],
        rating="low",
    )
    defaults.update(kwargs)
    return HallucinationReport(**defaults)


@pytest.fixture
def client():
    """Create a fresh TestClient for each test."""
    _chat_history.clear()
    with TestClient(app) as c:
        yield c
    _chat_history.clear()


# ─── Health endpoint ──────────────────────────────────────────────


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "gemini_configured" in data

    def test_health_response_shape(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert isinstance(data["gemini_configured"], bool)


# ─── Document upload endpoint ─────────────────────────────────────


class TestDocumentUpload:
    @patch("main.store_chunks", return_value=5)
    @patch("main.chunk_document")
    @patch("main.parse_document")
    def test_upload_pdf_success(self, mock_parse, mock_chunk, mock_store, client, sample_pdf_path):
        mock_parse.return_value = [(1, "Page 1 text"), (2, "Page 2 text")]
        mock_chunk.return_value = [
            MagicMock(chunk_id="c1", text="chunk 1", source="test.pdf", page=1, section=""),
            MagicMock(chunk_id="c2", text="chunk 2", source="test.pdf", page=1, section=""),
            MagicMock(chunk_id="c3", text="chunk 3", source="test.pdf", page=2, section=""),
            MagicMock(chunk_id="c4", text="chunk 4", source="test.pdf", page=2, section=""),
            MagicMock(chunk_id="c5", text="chunk 5", source="test.pdf", page=2, section=""),
        ]

        with open(sample_pdf_path, "rb") as f:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "indexed"
        assert data["num_chunks"] == 5
        assert data["num_pages"] == 2
        assert "document_id" in data
        assert data["filename"] == "test.pdf"

    def test_upload_unsupported_format(self, client):
        content = b"This is a text file."
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("readme.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    @patch("main.parse_document", return_value=[])
    def test_upload_empty_document(self, mock_parse, client, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("empty.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 400
        assert "Could not extract" in resp.json()["detail"]

    @patch("main.parse_document", side_effect=RuntimeError("GEMINI_API_KEY not set"))
    def test_upload_gemini_not_configured(self, mock_parse, client, sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert resp.status_code == 500
        assert "GEMINI_API_KEY" in resp.json()["detail"]


# ─── Document listing ─────────────────────────────────────────────


class TestDocumentListing:
    @patch("main.get_all_documents", return_value=[])
    def test_list_empty(self, mock_docs, client):
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("main.get_all_documents")
    def test_list_with_documents(self, mock_docs, client):
        mock_docs.return_value = [
            {"document_id": "d1", "filename": "policy.pdf", "num_chunks": 10, "num_pages": 3},
            {"document_id": "d2", "filename": "endorse.docx", "num_chunks": 5, "num_pages": 2},
        ]
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["document_id"] == "d1"
        assert data[1]["filename"] == "endorse.docx"


# ─── Document deletion ───────────────────────────────────────────


class TestDocumentDeletion:
    @patch("main.delete_document", return_value=True)
    def test_delete_success(self, mock_delete, client):
        resp = client.delete("/api/documents/doc-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deleted"
        assert data["document_id"] == "doc-001"

    @patch("main.delete_document", return_value=False)
    def test_delete_not_found(self, mock_delete, client):
        resp = client.delete("/api/documents/nonexistent")
        assert resp.status_code == 404


# ─── Chat endpoint ────────────────────────────────────────────────


class TestChatEndpoint:
    def test_empty_query_rejected(self, client):
        resp = client.post("/api/chat", json={"query": "", "session_id": "s1"})
        assert resp.status_code == 400

    def test_whitespace_query_rejected(self, client):
        resp = client.post("/api/chat", json={"query": "   ", "session_id": "s1"})
        assert resp.status_code == 400

    @patch("main.search", return_value=[])
    def test_no_documents_uploaded(self, mock_search, client):
        resp = client.post("/api/chat", json={"query": "What is the coverage?", "session_id": "s1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "No documents" in data["answer"]
        assert data["hallucination"]["rating"] == "high"
        assert data["actions"] == []

    @patch("main.get_uw_actions", return_value=[])
    @patch("main.analyze_hallucination")
    @patch("main.generate_rag_response", return_value="The coverage limit is $1,000,000.")
    @patch("main.search")
    def test_chat_full_pipeline(self, mock_search, mock_rag, mock_hall, mock_actions, client):
        mock_search.return_value = [
            {
                "text": "Coverage limit $1,000,000.",
                "source": "policy.pdf",
                "page": 1,
                "section": "COVERAGE",
                "similarity": 0.95,
                "document_id": "doc-001",
            }
        ]
        mock_hall.return_value = _make_hallucination_report(overall_score=85.0, retrieval_confidence=90.0)

        resp = client.post("/api/chat", json={"query": "What is the coverage limit?", "session_id": "s1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "The coverage limit is $1,000,000."
        assert len(data["sources"]) == 1
        assert data["session_id"] == "s1"

    @patch("main.get_uw_actions", return_value=[])
    @patch("main.analyze_hallucination")
    @patch("main.generate_rag_response", return_value="Answer.")
    @patch("main.search")
    def test_chat_updates_session_history(self, mock_search, mock_rag, mock_hall, mock_actions, client):
        mock_search.return_value = [
            {"text": "ctx", "source": "f.pdf", "page": 1, "section": "", "similarity": 0.9, "document_id": "d1"}
        ]
        mock_hall.return_value = _make_hallucination_report()

        client.post("/api/chat", json={"query": "Q1", "session_id": "test-session"})
        assert "test-session" in _chat_history
        assert len(_chat_history["test-session"]) == 2  # user + assistant

    @patch("main.search", side_effect=RuntimeError("GEMINI_API_KEY not configured"))
    def test_chat_gemini_error(self, mock_search, client):
        resp = client.post("/api/chat", json={"query": "test", "session_id": "s1"})
        assert resp.status_code == 500
        assert "GEMINI_API_KEY" in resp.json()["detail"]


# ─── Session management ──────────────────────────────────────────


class TestSessionManagement:
    def test_clear_session(self, client):
        _chat_history["s1"] = [{"role": "user", "content": "hello"}]
        resp = client.delete("/api/chat/session/s1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"
        assert "s1" not in _chat_history

    def test_clear_nonexistent_session(self, client):
        resp = client.delete("/api/chat/session/nonexistent")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"


# ─── CORS ─────────────────────────────────────────────────────────


class TestCORS:
    def test_cors_allows_localhost_4200(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:4200",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should allow the origin
        assert resp.status_code in (200, 204)

    def test_health_includes_cors_header(self, client):
        resp = client.get("/health", headers={"Origin": "http://localhost:4200"})
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:4200"


# ─── Source references in chat response ───────────────────────────


class TestSourceReferences:
    @patch("main.get_uw_actions", return_value=[])
    @patch("main.analyze_hallucination")
    @patch("main.generate_rag_response", return_value="Answer.")
    @patch("main.search")
    def test_sources_limited_to_five(self, mock_search, mock_rag, mock_hall, mock_actions, client):
        # Return 8 chunks but only top 5 should appear in sources
        mock_search.return_value = [
            {"text": f"chunk {i}", "source": "f.pdf", "page": i, "section": "",
             "similarity": 0.9 - i * 0.05, "document_id": f"d{i}"}
            for i in range(8)
        ]
        mock_hall.return_value = _make_hallucination_report()
        resp = client.post("/api/chat", json={"query": "test", "session_id": "s1"})
        data = resp.json()
        assert len(data["sources"]) <= 5

    @patch("main.get_uw_actions", return_value=[])
    @patch("main.analyze_hallucination")
    @patch("main.generate_rag_response", return_value="Answer.")
    @patch("main.search")
    def test_source_text_truncated_to_300(self, mock_search, mock_rag, mock_hall, mock_actions, client):
        long_text = "A" * 500
        mock_search.return_value = [
            {"text": long_text, "source": "f.pdf", "page": 1, "section": "",
             "similarity": 0.9, "document_id": "d1"}
        ]
        mock_hall.return_value = _make_hallucination_report()
        resp = client.post("/api/chat", json={"query": "test", "session_id": "s1"})
        data = resp.json()
        assert len(data["sources"][0]["text"]) <= 300
