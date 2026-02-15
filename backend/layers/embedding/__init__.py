from layers.embedding.embedding_factory import (
    get_embedding_provider,
    reset_embedding_provider,
    register_embedding_provider,
    list_registered_providers,
)
from layers.embedding.base import EmbeddingProvider


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured embedding provider."""
    return get_embedding_provider().embed_texts(texts)


def embed_query(query: str) -> list[float]:
    """Embed a single query using the configured embedding provider."""
    return get_embedding_provider().embed_query(query)
