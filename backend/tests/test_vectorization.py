from __future__ import annotations

"""
Tests for layers/vectorization/lance_store.py
Uses a temporary directory for LanceDB isolation and mocks embedding calls.
"""

import sys
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import layers.vectorization.lance_store as lance_store_module
from layers.vectorization.lance_store import (
    store_chunks,
    search,
    get_all_documents,
    delete_document,
    get_chunks_by_document,
    _get_db,
    _table_exists,
)


def _make_fake_embedding(dim: int = 768) -> list[float]:
    """Generate a random unit-norm embedding."""
    rng = np.random.RandomState(42)
    vec = rng.randn(dim).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


@pytest.fixture(autouse=True)
def isolated_lancedb(tmp_dir):
    """
    For every test, point LanceDB to a temp directory and reset the global state.
    This ensures full isolation between tests.
    """
    # Reset the default store instance state
    store = lance_store_module._default_store
    store._db = None
    store._document_registry = {}
    store._registry_loaded = False
    store._db_path = tmp_dir
    store._table_name = "test_chunks"

    yield tmp_dir

    # Cleanup
    store._db = None
    store._document_registry = {}
    store._registry_loaded = False


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "text": "The policy covers commercial property with limits of $1,000,000.",
            "source": "policy.pdf",
            "page": 1,
            "section": "COVERAGE",
        },
        {
            "chunk_id": str(uuid.uuid4()),
            "text": "Wind and hail endorsement applies a $500,000 sub-limit.",
            "source": "policy.pdf",
            "page": 2,
            "section": "ENDORSEMENTS",
        },
        {
            "chunk_id": str(uuid.uuid4()),
            "text": "Loss history shows 3 claims totaling $150,000 over 5 years.",
            "source": "policy.pdf",
            "page": 3,
            "section": "LOSS HISTORY",
        },
    ]


def _fake_embed_texts(texts):
    """Return deterministic embeddings based on text length."""
    embeddings = []
    for i, t in enumerate(texts):
        rng = np.random.RandomState(len(t) + i)
        vec = rng.randn(768).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        embeddings.append(vec.tolist())
    return embeddings


def _fake_embed_query(query):
    """Return a deterministic embedding for a query."""
    rng = np.random.RandomState(len(query))
    vec = rng.randn(768).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


# ─── store_chunks ─────────────────────────────────────────────────


class TestStoreChunks:
    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_store_returns_count(self, mock_embed, sample_chunks):
        count = store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        assert count == 3

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_store_empty_chunks_returns_zero(self, mock_embed):
        count = store_chunks([], "doc-001", "policy.pdf", 0)
        assert count == 0
        mock_embed.assert_not_called()

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_document_appears_in_registry(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        docs = get_all_documents()
        assert len(docs) == 1
        assert docs[0]["document_id"] == "doc-001"
        assert docs[0]["filename"] == "policy.pdf"
        assert docs[0]["num_chunks"] == 3
        assert docs[0]["num_pages"] == 3

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_store_multiple_documents(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks[:1], "doc-001", "file1.pdf", 1)
        store_chunks(sample_chunks[1:2], "doc-002", "file2.pdf", 1)
        docs = get_all_documents()
        assert len(docs) == 2

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_store_calls_embed_texts(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        mock_embed.assert_called_once()
        texts_arg = mock_embed.call_args[0][0]
        assert len(texts_arg) == 3


# ─── search ───────────────────────────────────────────────────────


class TestSearch:
    @patch("layers.vectorization.lance_store.embed_query", side_effect=_fake_embed_query)
    def test_search_empty_db_returns_empty(self, mock_embed):
        results = search("what is the coverage?")
        assert results == []

    @patch("layers.vectorization.lance_store.embed_query", side_effect=_fake_embed_query)
    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_search_returns_results(self, mock_embed_t, mock_embed_q, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        results = search("coverage limit")
        assert len(results) > 0
        for r in results:
            assert "text" in r
            assert "source" in r
            assert "page" in r
            assert "similarity" in r
            assert "document_id" in r

    @patch("layers.vectorization.lance_store.embed_query", side_effect=_fake_embed_query)
    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_search_respects_top_k(self, mock_embed_t, mock_embed_q, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        results = search("coverage", top_k=1)
        assert len(results) == 1

    @patch("layers.vectorization.lance_store.embed_query", side_effect=_fake_embed_query)
    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_search_result_fields(self, mock_embed_t, mock_embed_q, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        results = search("claims history", top_k=3)
        for r in results:
            assert isinstance(r["text"], str)
            assert isinstance(r["source"], str)
            assert isinstance(r["page"], int)
            assert isinstance(r["similarity"], float)


# ─── delete_document ──────────────────────────────────────────────


class TestDeleteDocument:
    def test_delete_from_empty_db_returns_false(self):
        assert delete_document("nonexistent") is False

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_delete_removes_from_registry(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        assert len(get_all_documents()) == 1

        result = delete_document("doc-001")
        assert result is True
        assert len(get_all_documents()) == 0

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    @patch("layers.vectorization.lance_store.embed_query", side_effect=_fake_embed_query)
    def test_deleted_chunks_not_in_search(self, mock_eq, mock_et, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        delete_document("doc-001")
        results = search("coverage")
        # After deletion, results should be empty or not contain doc-001
        for r in results:
            assert r.get("document_id") != "doc-001"


# ─── get_all_documents ────────────────────────────────────────────


class TestGetAllDocuments:
    def test_initially_empty(self):
        assert get_all_documents() == []

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_returns_all_stored(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks[:1], "d1", "f1.pdf", 1)
        store_chunks(sample_chunks[1:2], "d2", "f2.pdf", 1)
        store_chunks(sample_chunks[2:3], "d3", "f3.pdf", 1)
        docs = get_all_documents()
        assert len(docs) == 3
        ids = {d["document_id"] for d in docs}
        assert ids == {"d1", "d2", "d3"}


# ─── get_chunks_by_document ──────────────────────────────────────


class TestGetChunksByDocument:
    def test_empty_db(self):
        assert get_chunks_by_document("nonexistent") == []

    @patch("layers.vectorization.lance_store.embed_texts", side_effect=_fake_embed_texts)
    def test_returns_chunks_for_document(self, mock_embed, sample_chunks):
        store_chunks(sample_chunks, "doc-001", "policy.pdf", 3)
        chunks = get_chunks_by_document("doc-001")
        assert len(chunks) == 3
        for c in chunks:
            assert "text" in c
            assert "source" in c
            assert "page" in c
