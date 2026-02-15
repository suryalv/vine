from __future__ import annotations

"""
Tests for layers/embedding/embedding_factory.py
Verifies factory pattern, singleton behaviour, and backend selection.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.embedding.embedding_factory import (
    get_embedding_provider,
    reset_embedding_provider,
    register_embedding_provider,
    list_registered_providers,
)
from layers.embedding.base import EmbeddingProvider


# ─── Helpers ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test starts with a fresh singleton."""
    reset_embedding_provider()
    yield
    reset_embedding_provider()


# ─── Backend selection ───────────────────────────────────────────


class TestEmbeddingFactoryBackendSelection:
    @patch("config.EMBEDDING_BACKEND", "gemini")
    def test_returns_gemini_provider(self):
        provider = get_embedding_provider()
        from layers.embedding.gemini_embedder import GeminiEmbeddingProvider

        assert isinstance(provider, GeminiEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "bedrock")
    def test_returns_bedrock_provider(self):
        provider = get_embedding_provider()
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider

        assert isinstance(provider, BedrockEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "openai")
    def test_returns_openai_provider(self):
        provider = get_embedding_provider()
        from layers.embedding.openai_embedder import OpenAIEmbeddingProvider

        assert isinstance(provider, OpenAIEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "aws_bedrock")
    def test_aws_bedrock_alias_works(self):
        provider = get_embedding_provider()
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider

        assert isinstance(provider, BedrockEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "unknown_backend")
    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="unknown_backend"):
            get_embedding_provider()


# ─── Singleton behaviour ────────────────────────────────────────


class TestEmbeddingFactorySingleton:
    @patch("config.EMBEDDING_BACKEND", "gemini")
    def test_returns_same_instance(self):
        p1 = get_embedding_provider()
        p2 = get_embedding_provider()
        assert p1 is p2

    @patch("config.EMBEDDING_BACKEND", "gemini")
    def test_reset_clears_singleton(self):
        p1 = get_embedding_provider()
        reset_embedding_provider()
        p2 = get_embedding_provider()
        assert p1 is not p2


# ─── ABC compliance ─────────────────────────────────────────────


class TestEmbeddingProviderABC:
    def test_all_providers_are_embedding_providers(self):
        from layers.embedding.gemini_embedder import GeminiEmbeddingProvider
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider
        from layers.embedding.openai_embedder import OpenAIEmbeddingProvider

        assert issubclass(GeminiEmbeddingProvider, EmbeddingProvider)
        assert issubclass(BedrockEmbeddingProvider, EmbeddingProvider)
        assert issubclass(OpenAIEmbeddingProvider, EmbeddingProvider)

    def test_abc_has_required_methods(self):
        required = {"embed_texts", "embed_query"}
        abc_methods = {m for m in dir(EmbeddingProvider) if not m.startswith("_")}
        assert required.issubset(abc_methods)

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            EmbeddingProvider()


# ─── Case insensitivity / whitespace ────────────────────────────


class TestEmbeddingFactoryInputNormalization:
    @patch("config.EMBEDDING_BACKEND", "  Gemini  ")
    def test_whitespace_stripped(self):
        provider = get_embedding_provider()
        from layers.embedding.gemini_embedder import GeminiEmbeddingProvider

        assert isinstance(provider, GeminiEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "OPENAI")
    def test_case_insensitive(self):
        provider = get_embedding_provider()
        from layers.embedding.openai_embedder import OpenAIEmbeddingProvider

        assert isinstance(provider, OpenAIEmbeddingProvider)


# ─── Titan alias ─────────────────────────────────────────────────


class TestEmbeddingFactoryTitanAlias:
    @patch("config.EMBEDDING_BACKEND", "titan")
    def test_titan_returns_bedrock_provider(self):
        provider = get_embedding_provider()
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider

        assert isinstance(provider, BedrockEmbeddingProvider)

    @patch("config.EMBEDDING_BACKEND", "TITAN")
    def test_titan_case_insensitive(self):
        provider = get_embedding_provider()
        from layers.embedding.bedrock_embedder import BedrockEmbeddingProvider

        assert isinstance(provider, BedrockEmbeddingProvider)


# ─── Custom provider registration ───────────────────────────────


class TestEmbeddingFactoryCustomRegistration:
    def test_register_custom_provider(self):
        class StubProvider(EmbeddingProvider):
            def embed_texts(self, texts):
                return [[0.0] * 3 for _ in texts]

            def embed_query(self, query):
                return [0.0] * 3

        register_embedding_provider("stub_test", lambda: StubProvider())

        with patch("config.EMBEDDING_BACKEND", "stub_test"):
            provider = get_embedding_provider()
            assert isinstance(provider, StubProvider)
            assert provider.embed_query("hello") == [0.0] * 3

    def test_register_custom_with_aliases(self):
        class AnotherProvider(EmbeddingProvider):
            def embed_texts(self, texts):
                return [[1.0] for _ in texts]

            def embed_query(self, query):
                return [1.0]

        register_embedding_provider(
            "another_test", lambda: AnotherProvider(), aliases=["alt_test"]
        )

        with patch("config.EMBEDDING_BACKEND", "alt_test"):
            provider = get_embedding_provider()
            assert isinstance(provider, AnotherProvider)

    def test_list_registered_providers_includes_builtins(self):
        names = list_registered_providers()
        assert "gemini" in names
        assert "bedrock" in names
        assert "openai" in names
        assert "titan" in names
        assert "aws_bedrock" in names
        assert "aws" in names

    def test_list_registered_providers_includes_custom(self):
        class CustomProvider(EmbeddingProvider):
            def embed_texts(self, texts):
                return [[0.0] for _ in texts]

            def embed_query(self, query):
                return [0.0]

        register_embedding_provider("my_custom_test", lambda: CustomProvider())
        names = list_registered_providers()
        assert "my_custom_test" in names
