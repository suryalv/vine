from __future__ import annotations

"""
Hallucination Detection Algorithm
==================================

Multi-factor scoring system that evaluates how well an AI response
is grounded in the source documents.

Factors:
  1. Retrieval Confidence (0.25) — how relevant are the retrieved chunks?
  2. Response Grounding  (0.35) — per-sentence similarity to sources
  3. Numerical Fidelity  (0.20) — do numbers in the response match sources?
  4. Entity Consistency  (0.20) — do named entities match sources?

Output: HallucinationReport with overall score 0-100
  - 80-100  → LOW risk   (green)  — well grounded
  - 50-79   → MEDIUM risk (amber) — partially grounded
  - 0-49    → HIGH risk   (red)   — likely hallucinated
"""

import re
import numpy as np
from config import HALLUCINATION_WEIGHTS
from services.gemini_service import embed_texts, embed_query
from models.schemas import HallucinationReport, SentenceGrounding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def _split_sentences(text: str) -> list[str]:
    """Split response into individual sentences/claims."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]


def _extract_numbers(text: str) -> list[str]:
    """Extract all numerical values from text."""
    patterns = [
        r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B|K))?",  # Dollar amounts
        r"\d{1,3}(?:,\d{3})+(?:\.\d+)?",  # Large numbers with commas
        r"\d+\.?\d*\s*%",  # Percentages
        r"\d+\.?\d*",  # Plain numbers
    ]
    numbers = []
    for pattern in patterns:
        numbers.extend(re.findall(pattern, text))
    return list(set(numbers))


def _extract_entities(text: str) -> list[str]:
    """
    Extract likely named entities using pattern heuristics.
    Catches: company names, policy numbers, dates, addresses.
    """
    entities = []

    # Policy/reference numbers
    entities.extend(re.findall(r"[A-Z]{2,4}[-\s]?\d{4,}", text))

    # Dates
    entities.extend(re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", text))
    entities.extend(
        re.findall(
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            text,
        )
    )

    # Capitalized multi-word phrases (likely names/companies)
    entities.extend(re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}", text))

    return list(set(entities))


def _compute_retrieval_confidence(source_chunks: list[dict]) -> float:
    """Score based on how relevant the retrieved chunks are."""
    if not source_chunks:
        return 0.0
    similarities = [c.get("similarity", 0.0) for c in source_chunks]
    # Weighted average: top chunks matter more
    weights = [1.0 / (i + 1) for i in range(len(similarities))]
    weighted_sum = sum(s * w for s, w in zip(similarities, weights))
    total_weight = sum(weights)
    return min(1.0, weighted_sum / total_weight) * 100


def _compute_response_grounding(
    response: str, source_chunks: list[dict]
) -> tuple[float, list[SentenceGrounding]]:
    """
    Per-sentence grounding analysis.
    Embeds each response sentence and compares against source chunk embeddings.
    """
    sentences = _split_sentences(response)
    if not sentences or not source_chunks:
        return 0.0, []

    # Embed response sentences
    sentence_embeddings = embed_texts(sentences)

    # Embed source chunks (re-embed for fresh comparison)
    source_texts = [c["text"] for c in source_chunks]
    source_embeddings = embed_texts(source_texts)

    details: list[SentenceGrounding] = []
    scores: list[float] = []

    for sent, sent_emb in zip(sentences, sentence_embeddings):
        best_sim = 0.0
        best_source = ""
        for src, src_emb in zip(source_chunks, source_embeddings):
            sim = _cosine_similarity(sent_emb, src_emb)
            if sim > best_sim:
                best_sim = sim
                best_source = f"{src['source']}, p{src['page']}"

        # Threshold: >0.65 is considered grounded
        is_grounded = best_sim > 0.65
        score = min(1.0, best_sim / 0.8) * 100  # Normalize: 0.8 sim → 100%
        scores.append(score)

        details.append(
            SentenceGrounding(
                sentence=sent[:200],
                grounding_score=round(score, 1),
                best_source=best_source,
                is_grounded=is_grounded,
            )
        )

    avg_score = sum(scores) / len(scores) if scores else 0.0
    return avg_score, details


def _compute_numerical_fidelity(response: str, source_chunks: list[dict]) -> float:
    """Check if numbers in the response appear in source documents."""
    response_numbers = _extract_numbers(response)
    if not response_numbers:
        return 100.0  # No numbers to verify → perfect score

    source_text = " ".join(c["text"] for c in source_chunks)
    source_numbers = set(_extract_numbers(source_text))

    matched = 0
    for num in response_numbers:
        # Normalize for comparison
        num_clean = num.replace(",", "").replace("$", "").strip()
        if any(num_clean in sn.replace(",", "").replace("$", "").strip() for sn in source_numbers):
            matched += 1
        elif num in source_text:
            matched += 1

    return (matched / len(response_numbers)) * 100


def _compute_entity_consistency(response: str, source_chunks: list[dict]) -> float:
    """Check if named entities in the response appear in source documents."""
    response_entities = _extract_entities(response)
    if not response_entities:
        return 100.0  # No entities to verify → perfect score

    source_text = " ".join(c["text"] for c in source_chunks)

    matched = 0
    for entity in response_entities:
        if entity.lower() in source_text.lower():
            matched += 1

    return (matched / len(response_entities)) * 100


def analyze_hallucination(
    response: str,
    source_chunks: list[dict],
    query: str,
) -> HallucinationReport:
    """
    Run the full hallucination detection pipeline.

    Args:
        response: the AI-generated answer
        source_chunks: retrieved document chunks with similarity scores
        query: the original user question

    Returns:
        HallucinationReport with detailed grounding analysis
    """
    # 1. Retrieval confidence
    retrieval_score = _compute_retrieval_confidence(source_chunks)

    # 2. Response grounding (per-sentence)
    grounding_score, sentence_details = _compute_response_grounding(
        response, source_chunks
    )

    # 3. Numerical fidelity
    numerical_score = _compute_numerical_fidelity(response, source_chunks)

    # 4. Entity consistency
    entity_score = _compute_entity_consistency(response, source_chunks)

    # Weighted overall score
    w = HALLUCINATION_WEIGHTS
    overall = (
        retrieval_score * w["retrieval_confidence"]
        + grounding_score * w["response_grounding"]
        + numerical_score * w["numerical_fidelity"]
        + entity_score * w["entity_consistency"]
    )
    overall = round(min(100.0, max(0.0, overall)), 1)

    # Flag ungrounded sentences
    flagged = [
        d.sentence for d in sentence_details if not d.is_grounded
    ]

    # Determine risk rating
    if overall >= 80:
        rating = "low"
    elif overall >= 50:
        rating = "medium"
    else:
        rating = "high"

    return HallucinationReport(
        overall_score=overall,
        retrieval_confidence=round(retrieval_score, 1),
        response_grounding=round(grounding_score, 1),
        numerical_fidelity=round(numerical_score, 1),
        entity_consistency=round(entity_score, 1),
        sentence_details=sentence_details,
        flagged_claims=flagged[:10],  # Cap at 10
        rating=rating,
    )
