from __future__ import annotations

"""
Guidelines Layer — Public API
==============================
Exposes guideline storage, search, and enforcement functions.
"""

from layers.guidelines.guidelines_store import get_guidelines_store, reset_guidelines_store
from layers.guidelines.enforcer import enforce_guidelines


def store_guideline_chunks(chunks, guideline_id, filename, line_of_business, num_pages):
    """Embed and store guideline chunks."""
    return get_guidelines_store().store_guideline_chunks(
        chunks, guideline_id, filename, line_of_business, num_pages
    )


def search_guidelines(query, top_k=None):
    """Search all guideline chunks."""
    store = get_guidelines_store()
    if top_k is not None:
        return store.search_guidelines(query, top_k)
    return store.search_guidelines(query)


def search_guidelines_by_line(query, line_of_business, top_k=None):
    """Search guideline chunks filtered by line of business."""
    store = get_guidelines_store()
    if top_k is not None:
        return store.search_by_line(query, line_of_business, top_k)
    return store.search_by_line(query, line_of_business)


def list_guidelines():
    """Return metadata for all stored guidelines."""
    return get_guidelines_store().list_guidelines()


def delete_guideline(guideline_id):
    """Delete all chunks for a guideline."""
    return get_guidelines_store().delete_guideline(guideline_id)
