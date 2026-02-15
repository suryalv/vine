from __future__ import annotations

"""
Vectorization Layer — Public API
=================================
Exposes store_chunks, search, get_all_documents, delete_document,
get_chunks_by_document as module-level functions.

The underlying backend is determined by config.VECTOR_STORE_BACKEND.
"""

from layers.vectorization.factory import get_vector_store, reset_vector_store
from layers.vectorization.base import VectorStore


def store_chunks(chunks, document_id, filename, num_pages):
    """Embed and store document chunks in the configured vector store."""
    return get_vector_store().store_chunks(chunks, document_id, filename, num_pages)


def search(query, top_k=None):
    """Search for chunks most similar to the query."""
    store = get_vector_store()
    if top_k is not None:
        return store.search(query, top_k)
    return store.search(query)


def get_all_documents():
    """Return metadata for all uploaded documents."""
    return get_vector_store().get_all_documents()


def delete_document(document_id):
    """Delete all chunks for a given document."""
    return get_vector_store().delete_document(document_id)


def get_chunks_by_document(document_id):
    """Retrieve all chunks for a specific document."""
    return get_vector_store().get_chunks_by_document(document_id)
