from __future__ import annotations

"""
EMBEDDING LAYER — Gemini Backend
===================================
Google Gemini embedding implementation.
Implements the EmbeddingProvider ABC and also provides backward-compatible
module-level functions for existing callers.

Team Owner: ML / Embeddings Team
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_EMBED_MODEL
from layers.embedding.base import EmbeddingProvider


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider."""

    def __init__(
        self,
        model: str = GEMINI_EMBED_MODEL,
        api_key: str = GEMINI_API_KEY,
    ):
        self._model = model
        self._api_key = api_key
        self._configured = False

    def _ensure_configured(self) -> None:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        if not self._configured:
            genai.configure(api_key=self._api_key)
            self._configured = True

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._ensure_configured()
        embeddings: list[list[float]] = []
        BATCH = 100
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            result = genai.embed_content(
                model=self._model,
                content=batch,
                task_type="retrieval_document",
            )
            embeddings.extend(result["embedding"])
        return embeddings

    def embed_query(self, query: str) -> list[float]:
        self._ensure_configured()
        result = genai.embed_content(
            model=self._model,
            content=query,
            task_type="retrieval_query",
        )
        return result["embedding"]


# ─── Backward-compatible module-level functions ─────────────────
# Existing code and tests import these directly:
#   from layers.embedding.gemini_embedder import embed_texts, embed_query
# These thin wrappers reference module-level GEMINI_API_KEY / genai so
# that unit-test patches on those names keep working.


def _ensure_configured():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=GEMINI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    _ensure_configured()
    embeddings: list[list[float]] = []
    BATCH = 100
    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        result = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=batch,
            task_type="retrieval_document",
        )
        embeddings.extend(result["embedding"])
    return embeddings


def embed_query(query: str) -> list[float]:
    _ensure_configured()
    result = genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]
