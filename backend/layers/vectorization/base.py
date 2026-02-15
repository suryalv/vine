from __future__ import annotations

"""
Vector Store Abstract Base Class
=================================
Defines the interface that all vector store backends must implement.
Swap backends by changing config.VECTOR_STORE_BACKEND.

Team Owner: Data Infrastructure Team
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class VectorStore(ABC):
    """Abstract interface for vector store backends."""

    @abstractmethod
    def store_chunks(
        self,
        chunks: List[Dict],
        document_id: str,
        filename: str,
        num_pages: int,
    ) -> int:
        """Embed and store document chunks. Returns number of chunks stored."""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 8) -> List[Dict]:
        """Search for chunks similar to the query.
        Returns list of {text, source, page, section, similarity, document_id}.
        """
        ...

    @abstractmethod
    def get_all_documents(self) -> List[Dict]:
        """Return metadata for all documents.
        Returns list of {document_id, filename, num_chunks, num_pages}.
        """
        ...

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document. Returns True if found and deleted."""
        ...

    @abstractmethod
    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        """Retrieve all chunks for a specific document.
        Returns list of {text, source, page, vector}.
        """
        ...
