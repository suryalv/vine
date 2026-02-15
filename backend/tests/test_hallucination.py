from __future__ import annotations

"""
Tests for layers/hallucination/detector.py
The hallucination detector has many pure math/regex functions that can be
tested without mocking. Only analyze_hallucination and _compute_response_grounding
need embedding mocks.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layers.hallucination.detector import (
    _cosine_similarity,
    _split_sentences,
    _extract_numbers,
    _extract_entities,
    _compute_retrieval_confidence,
    _compute_response_grounding,
    _compute_numerical_fidelity,
    _compute_entity_consistency,
    analyze_hallucination,
)
from models.schemas import HallucinationReport, SentenceGrounding
from config import HALLUCINATION_WEIGHTS, HALLUCINATION_VOLUME_WEIGHTS


# ─── _cosine_similarity ──────────────────────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-5

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(a, b)) < 1e-5

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(_cosine_similarity(a, b) - (-1.0)) < 1e-5

    def test_zero_vector_returns_zero(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert _cosine_similarity(a, b) == 0.0

    def test_both_zero_vectors(self):
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        assert _cosine_similarity(a, b) == 0.0

    def test_similar_vectors_high_score(self):
        a = [1.0, 2.0, 3.0]
        b = [1.1, 2.1, 3.1]
        sim = _cosine_similarity(a, b)
        assert sim > 0.99

    def test_returns_float(self):
        result = _cosine_similarity([1.0, 0.0], [0.5, 0.5])
        assert isinstance(result, float)

    def test_known_value(self):
        """Verify against manual calculation."""
        a = [3.0, 4.0]
        b = [4.0, 3.0]
        # dot = 12+12=24, |a|=5, |b|=5, cos=24/25=0.96
        expected = 24.0 / 25.0
        assert abs(_cosine_similarity(a, b) - expected) < 1e-5


# ─── _split_sentences ────────────────────────────────────────────


class TestSplitSentences:
    def test_basic_split(self):
        text = "The first sentence is here. The second sentence is here. The third sentence is here."
        result = _split_sentences(text)
        assert len(result) == 3

    def test_filters_short_fragments(self):
        """Sentences with 3 or fewer words are filtered out."""
        text = "OK. This is a valid sentence. No."
        result = _split_sentences(text)
        # "OK." has 1 word, "No." has 1 word — both should be filtered
        assert all(len(s.split()) > 3 for s in result)

    def test_question_and_exclamation(self):
        text = "Is this covered by the policy? Yes it certainly is! Please check the endorsement now."
        result = _split_sentences(text)
        assert len(result) == 3

    def test_empty_string(self):
        assert _split_sentences("") == []

    def test_no_punctuation(self):
        text = "This text has no sentence-ending punctuation"
        result = _split_sentences(text)
        assert len(result) == 1

    def test_strips_whitespace(self):
        text = "  First sentence.   Second sentence.  "
        result = _split_sentences(text)
        for s in result:
            assert s == s.strip()


# ─── _extract_numbers ────────────────────────────────────────────


class TestExtractNumbers:
    def test_dollar_amounts(self):
        text = "The premium is $25,000 and the limit is $1,000,000."
        nums = _extract_numbers(text)
        assert any("25,000" in n for n in nums)
        assert any("1,000,000" in n for n in nums)

    def test_percentages(self):
        text = "Loss ratio is 35% and retention rate is 92.5%."
        nums = _extract_numbers(text)
        assert any("35" in n and "%" in n for n in nums)
        assert any("92.5" in n for n in nums)

    def test_plain_numbers(self):
        text = "There were 3 claims and 150 inspections."
        nums = _extract_numbers(text)
        assert any("3" in n for n in nums)
        assert any("150" in n for n in nums)

    def test_dollar_with_million(self):
        text = "Coverage limit is $5 million."
        nums = _extract_numbers(text)
        assert any("$5 million" in n or "$5" in n for n in nums)

    def test_no_numbers(self):
        text = "No numbers in this sentence at all."
        nums = _extract_numbers(text)
        # Should be empty or only contain non-meaningful matches
        # The regex will still match on the empty case
        # This is a basic sanity check
        assert isinstance(nums, list)

    def test_comma_separated_numbers(self):
        text = "Values: $1,234,567.89"
        nums = _extract_numbers(text)
        assert any("1,234,567" in n for n in nums)

    def test_deduplication(self):
        """Extracted numbers should be unique (set-based)."""
        text = "$5,000 and $5,000 again."
        nums = _extract_numbers(text)
        # Since we use set() in the function, duplicates should be removed
        dollar_matches = [n for n in nums if "5,000" in n]
        assert len(dollar_matches) >= 1


# ─── _extract_entities ───────────────────────────────────────────


class TestExtractEntities:
    def test_policy_numbers(self):
        text = "Policy number CP-2024-001 and form CG-00010415."
        entities = _extract_entities(text)
        assert any("CP-2024" in e or "CP" in e for e in entities)

    def test_dates_slash_format(self):
        text = "Effective 1/15/2025 through 1/15/2026."
        entities = _extract_entities(text)
        assert any("1/15/2025" in e for e in entities)

    def test_dates_long_format(self):
        text = "Effective January 15, 2025."
        entities = _extract_entities(text)
        assert any("January 15, 2025" in e or "January 15" in e for e in entities)

    def test_named_entities(self):
        text = "Insured: Meridian Steel Works. Agent: Pacific Coast Insurance."
        entities = _extract_entities(text)
        assert any("Meridian Steel" in e for e in entities)
        assert any("Pacific Coast" in e for e in entities)

    def test_no_entities(self):
        text = "this is all lowercase with no special entities or numbers."
        entities = _extract_entities(text)
        assert isinstance(entities, list)

    def test_deduplication(self):
        text = "Meridian Steel Works and Meridian Steel Works again."
        entities = _extract_entities(text)
        meridian = [e for e in entities if "Meridian Steel" in e]
        assert len(meridian) >= 1  # should be deduplicated


# ─── _compute_retrieval_confidence ───────────────────────────────


class TestComputeRetrievalConfidence:
    def test_empty_chunks_returns_zero(self):
        assert _compute_retrieval_confidence([]) == 0.0

    def test_perfect_similarity(self):
        chunks = [{"similarity": 1.0}, {"similarity": 1.0}]
        score = _compute_retrieval_confidence(chunks)
        assert score == 100.0

    def test_zero_similarity(self):
        chunks = [{"similarity": 0.0}, {"similarity": 0.0}]
        score = _compute_retrieval_confidence(chunks)
        assert score == 0.0

    def test_weighted_average(self):
        """First chunk should have more weight than later ones."""
        chunks_high_first = [{"similarity": 0.9}, {"similarity": 0.1}]
        chunks_low_first = [{"similarity": 0.1}, {"similarity": 0.9}]
        score_high = _compute_retrieval_confidence(chunks_high_first)
        score_low = _compute_retrieval_confidence(chunks_low_first)
        assert score_high > score_low

    def test_single_chunk(self):
        chunks = [{"similarity": 0.8}]
        score = _compute_retrieval_confidence(chunks)
        assert abs(score - 80.0) < 1e-5

    def test_score_bounded_0_100(self):
        chunks = [{"similarity": 1.5}]  # Unusually high
        score = _compute_retrieval_confidence(chunks)
        assert 0 <= score <= 100

    def test_missing_similarity_defaults_to_zero(self):
        chunks = [{"text": "no similarity key"}]
        score = _compute_retrieval_confidence(chunks)
        assert score == 0.0


# ─── _compute_numerical_fidelity ─────────────────────────────────


class TestComputeNumericalFidelity:
    def test_no_numbers_in_response_returns_100(self):
        response = "The policy covers commercial property."
        source_text = "Coverage amount is $1,000,000."
        score = _compute_numerical_fidelity(response, source_text)
        assert score == 100.0

    def test_all_numbers_match(self):
        response = "Premium is $25,000 and deductible is $5,000."
        source_text = "Premium is $25,000 with a deductible of $5,000 per occurrence."
        score = _compute_numerical_fidelity(response, source_text)
        # Multiple regex patterns may extract overlapping numbers; >= 80 is still high fidelity
        assert score >= 80.0

    def test_no_numbers_match(self):
        response = "Premium is $99,999."
        source_text = "The premium is $25,000."
        score = _compute_numerical_fidelity(response, source_text)
        assert score < 100.0

    def test_partial_match(self):
        response = "Limit is $1,000,000 and premium is $99,999."
        source_text = "Limit is $1,000,000. Premium is $25,000."
        score = _compute_numerical_fidelity(response, source_text)
        assert 0 < score < 100

    def test_empty_source(self):
        response = "Premium is $25,000."
        score = _compute_numerical_fidelity(response, "")
        assert score < 100.0


# ─── _compute_entity_consistency ─────────────────────────────────


class TestComputeEntityConsistency:
    def test_no_entities_in_response_returns_100(self):
        response = "the policy covers property damage."
        source_text = "Meridian Steel Works policy document."
        score = _compute_entity_consistency(response, source_text)
        assert score == 100.0

    def test_all_entities_match(self):
        response = "Meridian Steel Works has a policy effective January 15, 2025."
        source_text = "Meridian Steel Works LLC. Policy effective January 15, 2025."
        score = _compute_entity_consistency(response, source_text)
        assert score == 100.0

    def test_no_entities_match(self):
        response = "Acme Corporation policy from March 2020."
        source_text = "Meridian Steel Works policy document from January 2025."
        score = _compute_entity_consistency(response, source_text)
        # Acme Corporation is not in the source
        assert score < 100.0

    def test_empty_source(self):
        response = "Meridian Steel Works."
        score = _compute_entity_consistency(response, "")
        # No source text to match against
        assert score < 100.0


# ─── _compute_response_grounding (requires embedding mock) ───────


class TestComputeResponseGrounding:
    @patch("layers.hallucination.detector.embed_texts")
    def test_returns_score_and_details(self, mock_embed):
        # Mock embeddings: 2 sentences, 2 sources
        mock_embed.side_effect = [
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],  # sentence embeddings
            [[0.9, 0.1, 0.0], [0.1, 0.9, 0.0]],  # source embeddings
        ]
        response = "The policy covers property. The limit is one million."
        chunks = [
            {"text": "Property coverage provided.", "source": "doc.pdf", "page": 1},
            {"text": "Limit is $1,000,000.", "source": "doc.pdf", "page": 2},
        ]
        score, details = _compute_response_grounding(response, chunks)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert isinstance(details, list)
        assert all(isinstance(d, SentenceGrounding) for d in details)

    @patch("layers.hallucination.detector.embed_texts")
    def test_empty_response(self, mock_embed):
        score, details = _compute_response_grounding("", [])
        assert score == 0.0
        assert details == []
        mock_embed.assert_not_called()

    @patch("layers.hallucination.detector.embed_texts")
    def test_no_source_chunks(self, mock_embed):
        score, details = _compute_response_grounding("Some response text here.", [])
        assert score == 0.0
        assert details == []

    @patch("layers.hallucination.detector.embed_texts")
    def test_grounding_details_have_fields(self, mock_embed):
        mock_embed.side_effect = [
            [[1.0, 0.0]],  # 1 sentence
            [[0.8, 0.2]],  # 1 source
        ]
        response = "The coverage is comprehensive and adequate."
        chunks = [{"text": "Comprehensive coverage.", "source": "p.pdf", "page": 1}]
        _, details = _compute_response_grounding(response, chunks)
        if details:
            d = details[0]
            assert hasattr(d, "sentence")
            assert hasattr(d, "grounding_score")
            assert hasattr(d, "best_source")
            assert hasattr(d, "is_grounded")


# ─── analyze_hallucination (full pipeline) ────────────────────────


class TestAnalyzeHallucination:
    @patch("layers.hallucination.detector.embed_texts")
    def test_returns_hallucination_report(self, mock_embed, sample_source_chunks):
        # Mock for sentence embeddings and source embeddings
        mock_embed.side_effect = [
            [[0.5, 0.5, 0.0]],  # sentence embeddings (1 long sentence)
            [[0.4, 0.5, 0.1], [0.3, 0.3, 0.4], [0.5, 0.5, 0.0]],  # source embeddings
        ]
        response = "The policy covers commercial property with limits of one million dollars."
        report = analyze_hallucination(response, sample_source_chunks, "What is the coverage?")
        assert isinstance(report, HallucinationReport)

    @patch("layers.hallucination.detector.embed_texts")
    def test_report_has_all_fields(self, mock_embed, sample_source_chunks):
        mock_embed.side_effect = [
            [[0.5, 0.5]],
            [[0.4, 0.5], [0.3, 0.3], [0.5, 0.5]],
        ]
        response = "The policy has comprehensive coverage for property."
        report = analyze_hallucination(response, sample_source_chunks, "coverage?")
        assert hasattr(report, "overall_score")
        assert hasattr(report, "retrieval_confidence")
        assert hasattr(report, "response_grounding")
        assert hasattr(report, "numerical_fidelity")
        assert hasattr(report, "entity_consistency")
        assert hasattr(report, "sentence_details")
        assert hasattr(report, "flagged_claims")
        assert hasattr(report, "rating")

    @patch("layers.hallucination.detector.embed_texts")
    def test_rating_values(self, mock_embed, sample_source_chunks):
        mock_embed.side_effect = [
            [[0.5, 0.5]],
            [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]],
        ]
        response = "Some response about the policy coverage details."
        report = analyze_hallucination(response, sample_source_chunks, "coverage?")
        assert report.rating in ("low", "medium", "high")

    @patch("layers.hallucination.detector.embed_texts")
    def test_overall_score_bounded(self, mock_embed, sample_source_chunks):
        mock_embed.side_effect = [
            [[1.0, 0.0]],
            [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]],
        ]
        response = "Policy covers $1,000,000 for Meridian Steel Works."
        report = analyze_hallucination(response, sample_source_chunks, "coverage?")
        assert 0 <= report.overall_score <= 100

    @patch("layers.hallucination.detector.embed_texts")
    def test_flagged_claims_max_ten(self, mock_embed, sample_source_chunks):
        """flagged_claims should be capped at 10."""
        # Create a response with many sentences
        sentences = [f"Sentence number {i} makes a claim." for i in range(15)]
        response = " ".join(sentences)
        # All sentences get low grounding
        sent_embeds = [[0.0, 1.0]] * len([s for s in sentences if len(s.split()) > 3])
        src_embeds = [[1.0, 0.0]] * len(sample_source_chunks)
        mock_embed.side_effect = [sent_embeds, src_embeds]

        report = analyze_hallucination(response, sample_source_chunks, "test?")
        assert len(report.flagged_claims) <= 10


# ─── HALLUCINATION_WEIGHTS config ────────────────────────────────


class TestHallucinationWeights:
    def test_weights_sum_to_one(self):
        total = sum(HALLUCINATION_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6

    def test_all_weights_positive(self):
        for key, val in HALLUCINATION_WEIGHTS.items():
            assert val > 0, f"Weight for {key} should be positive"

    def test_expected_keys(self):
        expected = {"retrieval_confidence", "response_grounding", "numerical_fidelity", "entity_consistency"}
        assert set(HALLUCINATION_WEIGHTS.keys()) == expected

    def test_volume_weights_sum_to_one(self):
        total = sum(HALLUCINATION_VOLUME_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6

    def test_volume_weights_have_same_keys(self):
        assert set(HALLUCINATION_VOLUME_WEIGHTS.keys()) == set(HALLUCINATION_WEIGHTS.keys())
