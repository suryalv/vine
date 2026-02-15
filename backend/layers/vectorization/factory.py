from __future__ import annotations

"""
Vector Store Factory
====================
Reads VECTOR_STORE_BACKEND from config and returns the appropriate
VectorStore implementation. Uses lazy imports so you only need
dependencies for the backend you actually use.

Team Owner: Data Infrastructure Team
"""

from typing import Optional

from layers.vectorization.base import VectorStore

_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Return the configured vector store backend (singleton)."""
    global _instance
    if _instance is not None:
        return _instance

    from config import VECTOR_STORE_BACKEND

    backend = VECTOR_STORE_BACKEND.lower().strip()

    if backend == "lancedb":
        from layers.vectorization.lance_store import LanceDBStore
        _instance = LanceDBStore()

    elif backend == "pgvector":
        from layers.vectorization.pgvector_store import PgVectorStore
        _instance = PgVectorStore()

    elif backend in ("mongodb_atlas", "mongodb"):
        from layers.vectorization.mongodb_store import MongoDBAtlasStore
        _instance = MongoDBAtlasStore()

    else:
        raise ValueError(
            f"Unknown VECTOR_STORE_BACKEND: '{backend}'. "
            f"Supported: 'lancedb', 'pgvector', 'mongodb_atlas'"
        )

    return _instance


def reset_vector_store() -> None:
    """Reset the singleton — used in tests."""
    global _instance
    _instance = None
