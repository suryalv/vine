from __future__ import annotations

"""
Embedding Provider Abstract Base Class
========================================
Defines the interface all embedding backends must implement.
Swap backends by changing config.EMBEDDING_BACKEND.

Team Owner: ML / Embeddings Team
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts for document storage (retrieval_document task).

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query text for search (retrieval_query task).

        Args:
            query: The search query string.

        Returns:
            A single embedding vector.
        """
        ...
