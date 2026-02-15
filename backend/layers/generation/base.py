from __future__ import annotations

"""
LLM Provider Abstract Base Class
==================================
Defines the interface all LLM backends must implement.
Swap backends by changing config.LLM_BACKEND.

Team Owner: AI / LLM Team
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        chat_history: list[dict] | None = None,
    ) -> str:
        """Generate a text response given a prompt, optional system instructions,
        and optional chat history.

        Args:
            user_prompt: The user's message/prompt text.
            system_prompt: System-level instructions for the model.
            chat_history: List of {"role": "user"|"assistant", "content": str} dicts.

        Returns:
            Generated text string.
        """
        ...

    @abstractmethod
    def generate_simple(self, prompt: str) -> str:
        """Generate a response from a single prompt with no system/history.
        Used for structured extraction tasks (e.g., action extraction).

        Args:
            prompt: The full prompt text.

        Returns:
            Generated text string.
        """
        ...
