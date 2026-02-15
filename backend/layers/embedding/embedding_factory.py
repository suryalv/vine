from __future__ import annotations

"""
Embedding Provider Factory
============================
Reads EMBEDDING_BACKEND from config and returns the appropriate
EmbeddingProvider implementation. Uses lazy imports so you only need
dependencies for the backend you actually use.

Team Owner: ML / Embeddings Team
"""

from typing import Optional

from layers.embedding.base import EmbeddingProvider

_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider (singleton)."""
    global _instance
    if _instance is not None:
        return _instance

    from config import EMBEDDING_BACKEND

    backend = EMBEDDING_BACKEND.lower().strip()

    if backend == "gemini":
        from layers.embedding.gemini_embedder import GeminiEmbeddingProvider

        _instance = GeminiEmbeddingProvider()

    elif backend in ("bedrock", "aws_bedrock", "aws"):
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider

        _instance = BedrockEmbeddingProvider()

    elif backend == "openai":
        from layers.embedding.openai_embedder import OpenAIEmbeddingProvider

        _instance = OpenAIEmbeddingProvider()

    else:
        raise ValueError(
            f"Unknown EMBEDDING_BACKEND: '{backend}'. "
            f"Supported: 'gemini', 'bedrock', 'openai'"
        )

    return _instance


def reset_embedding_provider() -> None:
    """Reset the singleton — used in tests."""
    global _instance
    _instance = None
