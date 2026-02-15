from __future__ import annotations

"""
Tests for layers/generation/llm_factory.py
Verifies factory pattern, singleton behaviour, and backend selection.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.generation.llm_factory import get_llm_provider, reset_llm_provider
from layers.generation.base import LLMProvider


# ─── Helpers ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test starts with a fresh singleton."""
    reset_llm_provider()
    yield
    reset_llm_provider()


# ─── Backend selection ───────────────────────────────────────────


class TestLLMFactoryBackendSelection:
    @patch("config.LLM_BACKEND", "gemini")
    def test_returns_gemini_provider(self):
        provider = get_llm_provider()
        from layers.generation.gemini_llm import GeminiLLMProvider

        assert isinstance(provider, GeminiLLMProvider)

    @patch("config.LLM_BACKEND", "bedrock")
    def test_returns_bedrock_provider(self):
        provider = get_llm_provider()
        from layers.generation.bedrock_llm import BedrockLLMProvider

        assert isinstance(provider, BedrockLLMProvider)

    @patch("config.LLM_BACKEND", "openai")
    def test_returns_openai_provider(self):
        provider = get_llm_provider()
        from layers.generation.openai_llm import OpenAILLMProvider

        assert isinstance(provider, OpenAILLMProvider)

    @patch("config.LLM_BACKEND", "aws_bedrock")
    def test_aws_bedrock_alias_works(self):
        provider = get_llm_provider()
        from layers.generation.bedrock_llm import BedrockLLMProvider

        assert isinstance(provider, BedrockLLMProvider)

    @patch("config.LLM_BACKEND", "unknown_backend")
    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="unknown_backend"):
            get_llm_provider()


# ─── Singleton behaviour ────────────────────────────────────────


class TestLLMFactorySingleton:
    @patch("config.LLM_BACKEND", "gemini")
    def test_returns_same_instance(self):
        p1 = get_llm_provider()
        p2 = get_llm_provider()
        assert p1 is p2

    @patch("config.LLM_BACKEND", "gemini")
    def test_reset_clears_singleton(self):
        p1 = get_llm_provider()
        reset_llm_provider()
        p2 = get_llm_provider()
        assert p1 is not p2


# ─── ABC compliance ─────────────────────────────────────────────


class TestLLMProviderABC:
    def test_all_providers_are_llm_providers(self):
        from layers.generation.gemini_llm import GeminiLLMProvider
        from layers.generation.bedrock_llm import BedrockLLMProvider
        from layers.generation.openai_llm import OpenAILLMProvider

        assert issubclass(GeminiLLMProvider, LLMProvider)
        assert issubclass(BedrockLLMProvider, LLMProvider)
        assert issubclass(OpenAILLMProvider, LLMProvider)

    def test_abc_has_required_methods(self):
        required = {"generate", "generate_simple"}
        abc_methods = {m for m in dir(LLMProvider) if not m.startswith("_")}
        assert required.issubset(abc_methods)

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            LLMProvider()


# ─── Case insensitivity / whitespace ────────────────────────────


class TestLLMFactoryInputNormalization:
    @patch("config.LLM_BACKEND", "  Gemini  ")
    def test_whitespace_stripped(self):
        provider = get_llm_provider()
        from layers.generation.gemini_llm import GeminiLLMProvider

        assert isinstance(provider, GeminiLLMProvider)

    @patch("config.LLM_BACKEND", "OPENAI")
    def test_case_insensitive(self):
        provider = get_llm_provider()
        from layers.generation.openai_llm import OpenAILLMProvider

        assert isinstance(provider, OpenAILLMProvider)
