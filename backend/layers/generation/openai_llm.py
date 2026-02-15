from __future__ import annotations

"""
LLM Provider — OpenAI
========================
OpenAI GPT implementation of the LLMProvider interface.
Requires the openai package and a valid API key.

Team Owner: AI / LLM Team
"""

from layers.generation.base import LLMProvider
from config import OPENAI_API_KEY, OPENAI_CHAT_MODEL


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(
        self,
        model_name: str = OPENAI_CHAT_MODEL,
        api_key: str = OPENAI_API_KEY,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY environment variable is not set")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        chat_history: list[dict] | None = None,
    ) -> str:
        client = self._get_client()
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if chat_history:
            for msg in chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=self._model_name,
            messages=messages,
        )
        return response.choices[0].message.content

    def generate_simple(self, prompt: str) -> str:
        return self.generate(user_prompt=prompt)
