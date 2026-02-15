from __future__ import annotations

"""
GENERATION LAYER
================
Handles RAG response generation and action extraction using the configured LLM.
Constructs prompts with retrieved context and manages chat history.

Team Owner: AI / LLM Team
"""

from layers.generation.llm_factory import get_llm_provider


def generate_rag_response(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> str:
    """Generate a response grounded in the retrieved document chunks."""
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

    llm = get_llm_provider()
    return llm.generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        chat_history=chat_history,
    )


def extract_actions_prompt(query: str, answer: str, context_chunks: list[dict]) -> str:
    """Ask the LLM to extract structured UW actions from the answer + context."""
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

    llm = get_llm_provider()
    return llm.generate_simple(prompt)
