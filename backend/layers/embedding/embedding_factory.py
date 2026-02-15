from __future__ import annotations

"""
Embedding Provider Factory
============================
Registry-based factory that maps backend names to provider classes.
Built-in providers are registered at import time. Third-party providers
can be added via register_embedding_provider().

To add a custom embedding provider:
    1. Create a class that implements EmbeddingProvider (from layers.embedding.base)
    2. Register it before first use:

        from layers.embedding import register_embedding_provider

        register_embedding_provider(
            "my_provider",
            lambda: MyCustomEmbeddingProvider(),
            aliases=["custom", "mc"],
        )

    3. Set EMBEDDING_BACKEND=my_provider in your environment

Team Owner: ML / Embeddings Team
"""

from typing import Optional, Callable

from layers.embedding.base import EmbeddingProvider

_instance: Optional[EmbeddingProvider] = None

# Registry: lowercase alias -> lazy provider factory callable
_registry: dict[str, Callable[[], EmbeddingProvider]] = {}


def register_embedding_provider(
    name: str,
    factory: Callable[[], EmbeddingProvider],
    aliases: list[str] | None = None,
) -> None:
    """Register an embedding provider factory under one or more names.

    Args:
        name: Primary name (will be lowered automatically).
        factory: Zero-arg callable that returns an EmbeddingProvider instance.
        aliases: Optional additional names that map to the same factory.
    """
    _registry[name.lower().strip()] = factory
    for alias in (aliases or []):
        _registry[alias.lower().strip()] = factory


def _register_builtins() -> None:
    """Register the three built-in providers with their known aliases."""

    def _gemini():
        from layers.embedding.gemini_embedder import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider()

    def _bedrock():
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider
        return BedrockEmbeddingProvider()

    def _openai():
        from layers.embedding.openai_embedder import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()

    register_embedding_provider("gemini", _gemini)
    register_embedding_provider("bedrock", _bedrock, aliases=["aws_bedrock", "aws", "titan"])
    register_embedding_provider("openai", _openai)


# Register built-ins on module load
_register_builtins()


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider (singleton)."""
    global _instance
    if _instance is not None:
        return _instance

    from config import EMBEDDING_BACKEND

    backend = EMBEDDING_BACKEND.lower().strip()

    if backend not in _registry:
        supported = sorted(set(_registry.keys()))
        raise ValueError(
            f"Unknown EMBEDDING_BACKEND: '{backend}'. "
            f"Supported: {supported}"
        )

    _instance = _registry[backend]()
    return _instance


def reset_embedding_provider() -> None:
    """Reset the singleton — used in tests."""
    global _instance
    _instance = None


def list_registered_providers() -> list[str]:
    """Return all registered provider names (useful for CLI/debug)."""
    return sorted(set(_registry.keys()))
