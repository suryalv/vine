from __future__ import annotations

"""
Gemini API service — handles embeddings and RAG chat generation.
"""

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL, GEMINI_EMBED_MODEL


def _ensure_configured():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=GEMINI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Gemini's embedding model."""
    _ensure_configured()
    embeddings: list[list[float]] = []
    # Gemini embedding API supports batching up to 100 texts
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
    """Embed a single query text (uses retrieval_query task type)."""
    _ensure_configured()
    result = genai.embed_content(
        model=GEMINI_EMBED_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]


def generate_rag_response(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> str:
    """
    Generate a response grounded in the retrieved document chunks.

    Args:
        query: user question
        context_chunks: list of {text, source, page, similarity} dicts
        chat_history: optional prior conversation turns

    Returns:
        Generated answer string
    """
    _ensure_configured()

    # Build context block
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']}, Page {chunk['page']}]\n{chunk['text']}"
        )
    context_block = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are an expert underwriting AI assistant. You help commercial insurance underwriters analyze documents, extract key information, identify risks, and make informed decisions.

RULES:
- Answer ONLY based on the provided document context
- If information is not in the context, say "This information is not available in the uploaded documents"
- Always cite which source document and page your information comes from
- Use precise numbers and figures from the documents — never approximate
- Flag any risks, coverage gaps, or compliance issues you identify
- Be concise but thorough"""

    user_prompt = f"""DOCUMENT CONTEXT:
{context_block}

QUESTION: {query}

Provide a detailed, well-structured answer grounded in the document context above. Cite sources."""

    model = genai.GenerativeModel(
        GEMINI_CHAT_MODEL,
        system_instruction=system_prompt,
    )

    # Build conversation history if available
    history = []
    if chat_history:
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=history)
    response = chat.send_message(user_prompt)
    return response.text


def extract_actions(query: str, answer: str, context_chunks: list[dict]) -> str:
    """Ask Gemini to extract structured UW actions from the answer + context."""
    _ensure_configured()

    context_block = "\n".join(
        f"[{c['source']}, p{c['page']}]: {c['text'][:300]}" for c in context_chunks
    )

    prompt = f"""Based on this underwriting document analysis, extract actionable items for the underwriter.

CONTEXT SNIPPETS:
{context_block}

QUESTION: {query}
AI ANSWER: {answer}

Return a JSON array of actions. Each action must have:
- "action": short description of what to do
- "category": one of "coverage_gap", "risk_flag", "endorsement", "compliance", "pricing"
- "priority": one of "critical", "high", "medium", "low"
- "details": 1-2 sentence explanation
- "source_reference": which document/page this relates to

Return ONLY valid JSON array, no markdown fences. If no actions, return [].
"""

    model = genai.GenerativeModel(GEMINI_CHAT_MODEL)
    response = model.generate_content(prompt)
    return response.text
