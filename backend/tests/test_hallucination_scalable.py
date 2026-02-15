from __future__ import annotations

"""
Tests for hallucination detector scalability features:
  - TF-IDF pre-filtering
  - Batched embedding
  - Vectorized grounding
  - Volume-aware weight selection
  - Cached source context
"""

import sys
from pathlib import Path
from unittest.mock import patch, call

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.hallucination.detector import (
    _tokenize,
    _tfidf_prefilter,
    _batched_embed,
    _build_source_context,
    _compute_response_grounding,
    analyze_hallucination,
)
from config import (
    HALLUCINATION_WEIGHTS,
    HALLUCINATION_VOLUME_WEIGHTS,
    VOLUME_THRESHOLD,
    MAX_GROUNDING_CHUNKS,
)


# ─── _tokenize ──────────────────────────────────────────────────


class TestTokenize:
    def test_removes_stopwords(self):
        tokens = _tokenize("the quick brown fox is running")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens

    def test_lowercases(self):
        tokens = _tokenize("HELLO World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_removes_short_tokens(self):
        tokens = _tokenize("I am a big dog")
        assert "i" not in tokens  # single char
        assert "a" not in tokens  # single char
        assert "am" in tokens
        assert "big" in tokens

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_only_stopwords(self):
        tokens = _tokenize("the is a an")
        assert tokens == []


# ─── _tfidf_prefilter ───────────────────────────────────────────


class TestTfidfPrefilter:
    def test_returns_all_when_below_max(self):
        """If fewer chunks than max_chunks, return all of them."""
        chunks = [
            {"text": "coverage for property damage"},
            {"text": "liability limits and exclusions"},
        ]
        result = _tfidf_prefilter("property coverage", chunks, max_chunks=10)
        assert len(result) == 2

    def test_reduces_to_max_chunks(self):
        """With many chunks, result should be at most max_chunks."""
        chunks = [{"text": f"chunk number {i} about insurance"} for i in range(50)]
        result = _tfidf_prefilter("insurance policy coverage", chunks, max_chunks=5)
        assert len(result) == 5

    def test_selects_relevant_chunks(self):
        """Chunks mentioning query terms should rank higher."""
        chunks = [
            {"text": "this is about cooking recipes and food preparation"},
            {"text": "insurance coverage for commercial property damage"},
            {"text": "sports news and entertainment updates today"},
            {"text": "property insurance policy with comprehensive coverage"},
            {"text": "weather forecast for the upcoming week"},
        ]
        result = _tfidf_prefilter("property insurance coverage", chunks, max_chunks=2)
        result_texts = [c["text"] for c in result]
        # The insurance-related chunks should be selected
        assert any("insurance" in t for t in result_texts)
        assert any("property" in t for t in result_texts)

    def test_empty_response_returns_first_n(self):
        chunks = [{"text": f"chunk {i}"} for i in range(10)]
        result = _tfidf_prefilter("", chunks, max_chunks=3)
        assert len(result) == 3

    def test_preserves_chunk_structure(self):
        """Returned chunks should have the same dict structure."""
        chunks = [
            {"text": "property coverage", "source": "doc.pdf", "page": 1},
            {"text": "liability limits", "source": "doc.pdf", "page": 2},
            {"text": "exclusions list", "source": "doc.pdf", "page": 3},
        ]
        result = _tfidf_prefilter("property", chunks, max_chunks=2)
        for chunk in result:
            assert "text" in chunk
            assert "source" in chunk
            assert "page" in chunk


# ─── _batched_embed ──────────────────────────────────────────────


class TestBatchedEmbed:
    @patch("layers.hallucination.detector.embed_texts")
    def test_single_batch(self, mock_embed):
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        result = _batched_embed(["text1", "text2"], batch_size=10)
        assert len(result) == 2
        mock_embed.assert_called_once_with(["text1", "text2"])

    @patch("layers.hallucination.detector.embed_texts")
    def test_multiple_batches(self, mock_embed):
        mock_embed.side_effect = [
            [[0.1, 0.2], [0.3, 0.4]],  # batch 1
            [[0.5, 0.6]],               # batch 2
        ]
        result = _batched_embed(["t1", "t2", "t3"], batch_size=2)
        assert len(result) == 3
        assert mock_embed.call_count == 2

    @patch("layers.hallucination.detector.embed_texts")
    def test_empty_list(self, mock_embed):
        result = _batched_embed([], batch_size=10)
        assert result == []
        mock_embed.assert_not_called()

    @patch("layers.hallucination.detector.embed_texts")
    def test_exact_batch_size(self, mock_embed):
        mock_embed.side_effect = [
            [[0.1], [0.2]],
            [[0.3], [0.4]],
        ]
        result = _batched_embed(["a", "b", "c", "d"], batch_size=2)
        assert len(result) == 4
        assert mock_embed.call_count == 2


# ─── _build_source_context ──────────────────────────────────────


class TestBuildSourceContext:
    def test_concatenates_texts(self):
        chunks = [
            {"text": "first chunk"},
            {"text": "second chunk"},
            {"text": "third chunk"},
        ]
        result = _build_source_context(chunks)
        assert result == "first chunk second chunk third chunk"

    def test_empty_chunks(self):
        assert _build_source_context([]) == ""

    def test_single_chunk(self):
        chunks = [{"text": "only chunk"}]
        assert _build_source_context(chunks) == "only chunk"


# ─── Volume-aware weight selection ──────────────────────────────


class TestVolumeAwareWeights:
    @patch("layers.hallucination.detector.embed_texts")
    def test_standard_weights_below_threshold(self, mock_embed):
        """Below VOLUME_THRESHOLD, standard weights should be used."""
        mock_embed.side_effect = [
            [[0.5, 0.5]],           # sentence embeddings
            [[0.5, 0.5]] * 3,       # source embeddings
        ]
        chunks = [
            {"text": "coverage text", "source": "doc.pdf", "page": 1, "similarity": 0.9},
            {"text": "limit text", "source": "doc.pdf", "page": 2, "similarity": 0.8},
            {"text": "deductible text", "source": "doc.pdf", "page": 3, "similarity": 0.7},
        ]
        assert len(chunks) < VOLUME_THRESHOLD
        report = analyze_hallucination("The policy covers property.", chunks, "coverage?")
        # We can't directly check which weights were used, but we verify it runs without error
        assert 0 <= report.overall_score <= 100

    @patch("layers.hallucination.detector.embed_texts")
    def test_volume_weights_above_threshold(self, mock_embed):
        """At or above VOLUME_THRESHOLD, volume weights should be used."""
        num_chunks = VOLUME_THRESHOLD + 5
        mock_embed.side_effect = [
            [[0.5, 0.5]],                    # sentence embeddings
            [[0.5, 0.5]] * min(num_chunks, MAX_GROUNDING_CHUNKS),  # source embeddings (after TF-IDF filter)
        ]
        chunks = [
            {
                "text": f"chunk {i} about property insurance",
                "source": "doc.pdf",
                "page": i % 10 + 1,
                "similarity": 0.8,
            }
            for i in range(num_chunks)
        ]
        report = analyze_hallucination("The policy covers property.", chunks, "coverage?")
        assert 0 <= report.overall_score <= 100

    def test_volume_weights_differ_from_standard(self):
        """Volume weights should have different values for retrieval_confidence."""
        assert (
            HALLUCINATION_VOLUME_WEIGHTS["retrieval_confidence"]
            != HALLUCINATION_WEIGHTS["retrieval_confidence"]
        )


# ─── Vectorized grounding (integration) ─────────────────────────


class TestVectorizedGrounding:
    @patch("layers.hallucination.detector.embed_texts")
    def test_grounding_returns_correct_count(self, mock_embed):
        """Number of sentence details should match number of qualifying sentences."""
        mock_embed.side_effect = [
            [[1.0, 0.0], [0.0, 1.0]],  # 2 sentence embeddings
            [[0.9, 0.1], [0.1, 0.9]],  # 2 source embeddings
        ]
        response = "The first sentence about property. The second sentence about limits."
        chunks = [
            {"text": "property coverage", "source": "a.pdf", "page": 1},
            {"text": "policy limits", "source": "b.pdf", "page": 2},
        ]
        score, details = _compute_response_grounding(response, chunks)
        assert len(details) == 2
        assert all(hasattr(d, "grounding_score") for d in details)

    @patch("layers.hallucination.detector.embed_texts")
    def test_high_similarity_means_grounded(self, mock_embed):
        """Near-identical embeddings should produce high grounding scores."""
        mock_embed.side_effect = [
            [[1.0, 0.0, 0.0]],          # 1 sentence
            [[0.99, 0.01, 0.0]],         # 1 source (very similar)
        ]
        response = "The property is covered under the main policy."
        chunks = [{"text": "property coverage", "source": "a.pdf", "page": 1}]
        score, details = _compute_response_grounding(response, chunks)
        assert score > 80.0
        assert details[0].is_grounded is True

    @patch("layers.hallucination.detector.embed_texts")
    def test_low_similarity_means_ungrounded(self, mock_embed):
        """Orthogonal embeddings should produce low grounding scores."""
        mock_embed.side_effect = [
            [[1.0, 0.0, 0.0]],          # 1 sentence
            [[0.0, 0.0, 1.0]],          # 1 source (orthogonal)
        ]
        response = "The property is covered under the main policy."
        chunks = [{"text": "unrelated text", "source": "a.pdf", "page": 1}]
        score, details = _compute_response_grounding(response, chunks)
        assert score < 50.0
        assert details[0].is_grounded is False
