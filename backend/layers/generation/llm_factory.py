from __future__ import annotations

"""
LLM Provider Factory
=====================
Reads LLM_BACKEND from config and returns the appropriate
LLMProvider implementation. Uses lazy imports so you only need
dependencies for the backend you actually use.

Team Owner: AI / LLM Team
"""

from typing import Optional

from layers.generation.base import LLMProvider

_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider (singleton)."""
    global _instance
    if _instance is not None:
        return _instance

    from config import LLM_BACKEND

    backend = LLM_BACKEND.lower().strip()

    if backend == "gemini":
        from layers.generation.gemini_llm import GeminiLLMProvider

        _instance = GeminiLLMProvider()

    elif backend in ("bedrock", "aws_bedrock", "aws"):
        from layers.generation.bedrock_llm import BedrockLLMProvider

        _instance = BedrockLLMProvider()

    elif backend == "openai":
        from layers.generation.openai_llm import OpenAILLMProvider

        _instance = OpenAILLMProvider()

    else:
        raise ValueError(
            f"Unknown LLM_BACKEND: '{backend}'. "
            f"Supported: 'gemini', 'bedrock', 'openai'"
        )

    return _instance


def reset_llm_provider() -> None:
    """Reset the singleton — used in tests."""
    global _instance
    _instance = None
