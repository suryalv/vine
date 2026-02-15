from __future__ import annotations

"""
Tests for layers/embedding/gemini_embedder.py
All Gemini API calls are mocked — these tests verify logic, batching, and error handling.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.embedding.gemini_embedder import embed_texts, embed_query, _ensure_configured


# ─── _ensure_configured ──────────────────────────────────────────


class TestEnsureConfigured:
    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "")
    def test_raises_when_no_api_key(self):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            _ensure_configured()

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key-123")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_configures_genai_with_key(self, mock_genai):
        _ensure_configured()
        mock_genai.configure.assert_called_once_with(api_key="test-key-123")


# ─── embed_texts ──────────────────────────────────────────────────


class TestEmbedTexts:
    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_returns_list_of_embeddings(self, mock_genai):
        fake_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_genai.embed_content.return_value = {"embedding": fake_embeddings}

        result = embed_texts(["text one", "text two"])
        assert result == fake_embeddings
        assert len(result) == 2

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_calls_with_correct_task_type(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [[0.1]]}
        embed_texts(["hello"])
        call_kwargs = mock_genai.embed_content.call_args
        assert call_kwargs.kwargs.get("task_type") == "retrieval_document" or \
               call_kwargs[1].get("task_type") == "retrieval_document"

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_batching_over_100(self, mock_genai):
        """Texts are batched in groups of 100."""
        texts = [f"text {i}" for i in range(250)]
        batch1 = [[float(i)] for i in range(100)]
        batch2 = [[float(i)] for i in range(100, 200)]
        batch3 = [[float(i)] for i in range(200, 250)]
        mock_genai.embed_content.side_effect = [
            {"embedding": batch1},
            {"embedding": batch2},
            {"embedding": batch3},
        ]

        result = embed_texts(texts)
        assert len(result) == 250
        assert mock_genai.embed_content.call_count == 3

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_empty_list(self, mock_genai):
        """Empty input should return empty output without calling API."""
        result = embed_texts([])
        assert result == []
        mock_genai.embed_content.assert_not_called()

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_single_text(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [[1.0, 2.0, 3.0]]}
        result = embed_texts(["single text"])
        assert len(result) == 1
        assert result[0] == [1.0, 2.0, 3.0]

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_uses_correct_model(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [[0.0]]}
        embed_texts(["test"])
        call_args = mock_genai.embed_content.call_args
        # Model should be from config
        model_used = call_args.kwargs.get("model") or call_args[1].get("model")
        assert model_used is not None


# ─── embed_query ──────────────────────────────────────────────────


class TestEmbedQuery:
    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_returns_single_embedding(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [0.1, 0.2, 0.3]}
        result = embed_query("what is the coverage?")
        assert result == [0.1, 0.2, 0.3]

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_uses_retrieval_query_task(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [0.0]}
        embed_query("test query")
        call_kwargs = mock_genai.embed_content.call_args
        task = call_kwargs.kwargs.get("task_type") or call_kwargs[1].get("task_type")
        assert task == "retrieval_query"

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "test-key")
    @patch("layers.embedding.gemini_embedder.genai")
    def test_passes_query_as_content(self, mock_genai):
        mock_genai.embed_content.return_value = {"embedding": [0.0]}
        embed_query("my search query")
        call_kwargs = mock_genai.embed_content.call_args
        content = call_kwargs.kwargs.get("content") or call_kwargs[1].get("content")
        assert content == "my search query"

    @patch("layers.embedding.gemini_embedder.GEMINI_API_KEY", "")
    def test_raises_without_api_key(self):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            embed_query("test")
