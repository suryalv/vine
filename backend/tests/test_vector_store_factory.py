from __future__ import annotations

"""
Tests for layers/vectorization/factory.py
Verifies factory pattern, singleton behaviour, and backend selection.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.vectorization.factory import get_vector_store, reset_vector_store
from layers.vectorization.base import VectorStore


# ─── Helpers ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test starts with a fresh singleton."""
    reset_vector_store()
    yield
    reset_vector_store()


# ─── Backend selection ───────────────────────────────────────────


class TestFactoryBackendSelection:
    @patch("config.VECTOR_STORE_BACKEND", "lancedb")
    def test_returns_lancedb_store(self):
        store = get_vector_store()
        from layers.vectorization.lance_store import LanceDBStore
        assert isinstance(store, LanceDBStore)

    @patch("config.VECTOR_STORE_BACKEND", "pgvector")
    def test_returns_pgvector_store(self):
        store = get_vector_store()
        from layers.vectorization.pgvector_store import PgVectorStore
        assert isinstance(store, PgVectorStore)

    @patch("config.VECTOR_STORE_BACKEND", "mongodb_atlas")
    def test_returns_mongodb_store(self):
        store = get_vector_store()
        from layers.vectorization.mongodb_store import MongoDBAtlasStore
        assert isinstance(store, MongoDBAtlasStore)

    @patch("config.VECTOR_STORE_BACKEND", "mongodb")
    def test_mongodb_alias_works(self):
        store = get_vector_store()
        from layers.vectorization.mongodb_store import MongoDBAtlasStore
        assert isinstance(store, MongoDBAtlasStore)

    @patch("config.VECTOR_STORE_BACKEND", "unknown_backend")
    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="unknown_backend"):
            get_vector_store()


# ─── Singleton behaviour ────────────────────────────────────────


class TestFactorySingleton:
    @patch("config.VECTOR_STORE_BACKEND", "lancedb")
    def test_returns_same_instance(self):
        store1 = get_vector_store()
        store2 = get_vector_store()
        assert store1 is store2

    @patch("config.VECTOR_STORE_BACKEND", "lancedb")
    def test_reset_clears_singleton(self):
        store1 = get_vector_store()
        reset_vector_store()
        store2 = get_vector_store()
        assert store1 is not store2


# ─── ABC compliance ─────────────────────────────────────────────


class TestVectorStoreABC:
    def test_all_backends_are_vector_stores(self):
        from layers.vectorization.lance_store import LanceDBStore
        from layers.vectorization.pgvector_store import PgVectorStore
        from layers.vectorization.mongodb_store import MongoDBAtlasStore

        assert issubclass(LanceDBStore, VectorStore)
        assert issubclass(PgVectorStore, VectorStore)
        assert issubclass(MongoDBAtlasStore, VectorStore)

    def test_abc_has_required_methods(self):
        required = {"store_chunks", "search", "get_all_documents", "delete_document", "get_chunks_by_document"}
        abc_methods = {m for m in dir(VectorStore) if not m.startswith("_")}
        assert required.issubset(abc_methods)

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            VectorStore()


# ─── Case insensitivity / whitespace ────────────────────────────


class TestFactoryInputNormalization:
    @patch("config.VECTOR_STORE_BACKEND", "  LanceDB  ")
    def test_whitespace_stripped(self):
        store = get_vector_store()
        from layers.vectorization.lance_store import LanceDBStore
        assert isinstance(store, LanceDBStore)

    @patch("config.VECTOR_STORE_BACKEND", "PGVECTOR")
    def test_case_insensitive(self):
        store = get_vector_store()
        from layers.vectorization.pgvector_store import PgVectorStore
        assert isinstance(store, PgVectorStore)
