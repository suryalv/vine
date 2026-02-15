from __future__ import annotations

"""
EMBEDDING LAYER — OpenAI Backend
====================================
OpenAI text-embedding-3 implementation.
Requires the openai package and a valid API key.

Team Owner: ML / Embeddings Team
"""

from layers.embedding.base import EmbeddingProvider
from config import OPENAI_API_KEY, OPENAI_EMBED_MODEL


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(
        self,
        model: str = OPENAI_EMBED_MODEL,
        api_key: str = OPENAI_API_KEY,
    ):
        self._model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY environment variable is not set")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        embeddings: list[list[float]] = []
        BATCH = 100
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            response = client.embeddings.create(model=self._model, input=batch)
            for item in response.data:
                embeddings.append(item.embedding)
        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
