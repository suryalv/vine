from __future__ import annotations

"""
HALLUCINATION LAYER — Scalable Multi-Factor Scoring
=====================================================
Evaluates how well an AI response is grounded in source documents.

Factors:
  1. Retrieval Confidence (0.25) — how relevant are the retrieved chunks?
  2. Response Grounding  (0.35) — per-sentence similarity to sources
  3. Numerical Fidelity  (0.20) — do numbers in response match sources?
  4. Entity Consistency  (0.20) — do named entities match sources?

Scalability features:
  - TF-IDF pre-filtering: narrows 500+ chunks to top-20 before embedding
  - Vectorized similarity: numpy matrix ops instead of nested loops
  - Batched embedding: configurable batch size for API calls
  - Cached source text: built once, shared across sub-functions
  - Volume-aware weights: adjusted for large corpus scenarios

Output: HallucinationReport with overall score 0-100
  - 80-100 → LOW risk   (green)
  - 50-79  → MEDIUM risk (amber)
  - 0-49   → HIGH risk   (red)

Team Owner: AI Safety / Trust Team
"""

import math
import re
from collections import Counter
from typing import List, Tuple

import numpy as np

from config import (
    HALLUCINATION_WEIGHTS,
    HALLUCINATION_VOLUME_WEIGHTS,
    MAX_GROUNDING_CHUNKS,
    GROUNDING_THRESHOLD,
    EMBEDDING_BATCH_SIZE,
    VOLUME_THRESHOLD,
)
from layers.embedding import embed_texts
from models.schemas import HallucinationReport, SentenceGrounding


# ─── Low-level helpers ────────────────────────────────────────────


def _cosine_similarity(a: list, b: list) -> float:
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def _split_sentences(text: str) -> list:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]


def _extract_numbers(text: str) -> list:
    patterns = [
        r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B|K))?",
        r"\d{1,3}(?:,\d{3})+(?:\.\d+)?",
        r"\d+\.?\d*\s*%",
        r"\d+\.?\d*",
    ]
    numbers = []
    for pattern in patterns:
        numbers.extend(re.findall(pattern, text))
    return list(set(numbers))


def _extract_entities(text: str) -> list:
    entities = []
    entities.extend(re.findall(r"[A-Z]{2,4}[-\s]?\d{4,}", text))
    entities.extend(re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", text))
    entities.extend(
        re.findall(
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            text,
        )
    )
    entities.extend(re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}", text))
    return list(set(entities))


# ─── Scalability helpers ─────────────────────────────────────────


_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "again", "further", "then", "once", "and",
    "but", "or", "nor", "not", "so", "yet", "both", "either", "neither",
    "each", "every", "all", "any", "few", "more", "most", "other", "some",
    "such", "no", "only", "own", "same", "than", "too", "very", "just",
    "because", "if", "when", "where", "how", "what", "which", "who",
    "whom", "this", "that", "these", "those", "it", "its",
})


def _tokenize(text: str) -> list:
    """Simple whitespace + lowercase tokenizer with stopword removal."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _tfidf_prefilter(
    response: str, source_chunks: list, max_chunks: int = MAX_GROUNDING_CHUNKS
) -> list:
    """
    Pre-filter source chunks using TF-IDF scoring to select the most
    relevant chunks BEFORE expensive embedding-based comparison.
    Reduces 500+ chunks to ~20.
    """
    if len(source_chunks) <= max_chunks:
        return source_chunks

    response_tokens = _tokenize(response)
    if not response_tokens:
        return source_chunks[:max_chunks]

    num_docs = len(source_chunks)
    doc_freq: Counter = Counter()
    chunk_tokens_list = []
    for chunk in source_chunks:
        tokens = set(_tokenize(chunk["text"]))
        chunk_tokens_list.append(tokens)
        for token in tokens:
            doc_freq[token] += 1

    response_token_counts = Counter(response_tokens)
    scored_chunks = []
    for i, chunk in enumerate(source_chunks):
        chunk_tokens = _tokenize(chunk["text"])
        chunk_counts = Counter(chunk_tokens)
        score = 0.0
        for token in response_token_counts:
            if token in chunk_counts:
                tf = chunk_counts[token] / max(len(chunk_tokens), 1)
                idf = math.log((num_docs + 1) / (doc_freq.get(token, 0) + 1))
                score += tf * idf * response_token_counts[token]
        scored_chunks.append((score, i, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item[2] for item in scored_chunks[:max_chunks]]


def _batched_embed(texts: list, batch_size: int = EMBEDDING_BATCH_SIZE) -> list:
    """Embed texts in configurable batches for better memory control."""
    if not texts:
        return []
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch))
    return all_embeddings


def _build_source_context(source_chunks: list) -> str:
    """Build concatenated source text once, shared across sub-functions."""
    return " ".join(c["text"] for c in source_chunks)


# ─── Factor computation ──────────────────────────────────────────


def _compute_retrieval_confidence(source_chunks: list) -> float:
    if not source_chunks:
        return 0.0
    similarities = [c.get("similarity", 0.0) for c in source_chunks]
    weights = [1.0 / (i + 1) for i in range(len(similarities))]
    weighted_sum = sum(s * w for s, w in zip(similarities, weights))
    total_weight = sum(weights)
    return min(1.0, weighted_sum / total_weight) * 100


def _compute_response_grounding(
    response: str,
    source_chunks: list,
    grounding_threshold: float = GROUNDING_THRESHOLD,
    max_chunks: int = MAX_GROUNDING_CHUNKS,
) -> Tuple[float, List[SentenceGrounding]]:
    """
    Per-sentence grounding analysis with scalability optimizations:
    1. Pre-filter source chunks via TF-IDF (500 -> 20)
    2. Batch embedding calls
    3. Vectorized cosine similarity using numpy matrix ops
    """
    sentences = _split_sentences(response)
    if not sentences or not source_chunks:
        return 0.0, []

    # Step 1: Pre-filter chunks to most relevant subset
    filtered_chunks = _tfidf_prefilter(response, source_chunks, max_chunks)

    # Step 2: Batch embed sentences and filtered source chunks
    sentence_embeddings = _batched_embed(sentences)
    source_texts = [c["text"] for c in filtered_chunks]
    source_embeddings = _batched_embed(source_texts)

    # Step 3: Vectorized similarity matrix (sentences x sources)
    sent_matrix = np.array(sentence_embeddings, dtype=np.float32)
    src_matrix = np.array(source_embeddings, dtype=np.float32)

    sent_norms = np.linalg.norm(sent_matrix, axis=1, keepdims=True)
    src_norms = np.linalg.norm(src_matrix, axis=1, keepdims=True)
    sent_norms[sent_norms == 0] = 1.0
    src_norms[src_norms == 0] = 1.0
    sent_normed = sent_matrix / sent_norms
    src_normed = src_matrix / src_norms

    similarity_matrix = sent_normed @ src_normed.T

    # Step 4: Build grounding details
    details: List[SentenceGrounding] = []
    scores: list = []

    for i, sent in enumerate(sentences):
        best_idx = int(np.argmax(similarity_matrix[i]))
        best_sim = float(similarity_matrix[i, best_idx])
        best_chunk = filtered_chunks[best_idx]
        best_source = f"{best_chunk['source']}, p{best_chunk['page']}"

        is_grounded = best_sim > grounding_threshold
        score = min(1.0, best_sim / 0.8) * 100
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


def _compute_numerical_fidelity(response: str, source_text: str) -> float:
    """Check if numbers in the response appear in source documents."""
    response_numbers = _extract_numbers(response)
    if not response_numbers:
        return 100.0
    source_numbers = set(_extract_numbers(source_text))
    matched = 0
    for num in response_numbers:
        num_clean = num.replace(",", "").replace("$", "").strip()
        if any(num_clean in sn.replace(",", "").replace("$", "").strip() for sn in source_numbers):
            matched += 1
        elif num in source_text:
            matched += 1
    return (matched / len(response_numbers)) * 100


def _compute_entity_consistency(response: str, source_text: str) -> float:
    """Check if named entities in the response appear in source documents."""
    response_entities = _extract_entities(response)
    if not response_entities:
        return 100.0
    matched = 0
    source_lower = source_text.lower()
    for entity in response_entities:
        if entity.lower() in source_lower:
            matched += 1
    return (matched / len(response_entities)) * 100


# ─── Main entry point ────────────────────────────────────────────


def analyze_hallucination(
    response: str,
    source_chunks: list,
    query: str,
) -> HallucinationReport:
    """
    Run the full hallucination detection pipeline with scalability optimizations.
    """
    # Pre-build shared source text
    source_text = _build_source_context(source_chunks)

    # 1. Retrieval confidence (cheap — uses existing similarity scores)
    retrieval_score = _compute_retrieval_confidence(source_chunks)

    # 2. Response grounding (optimized with pre-filtering + vectorized ops)
    grounding_score, sentence_details = _compute_response_grounding(
        response, source_chunks
    )

    # 3. Numerical fidelity (uses pre-built source_text)
    numerical_score = _compute_numerical_fidelity(response, source_text)

    # 4. Entity consistency (uses pre-built source_text)
    entity_score = _compute_entity_consistency(response, source_text)

    # 5. Volume-aware weight selection
    is_high_volume = len(source_chunks) >= VOLUME_THRESHOLD
    w = HALLUCINATION_VOLUME_WEIGHTS if is_high_volume else HALLUCINATION_WEIGHTS

    overall = (
        retrieval_score * w["retrieval_confidence"]
        + grounding_score * w["response_grounding"]
        + numerical_score * w["numerical_fidelity"]
        + entity_score * w["entity_consistency"]
    )
    overall = round(min(100.0, max(0.0, overall)), 1)

    flagged = [d.sentence for d in sentence_details if not d.is_grounded]

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
        flagged_claims=flagged[:10],
        rating=rating,
    )
