from __future__ import annotations

"""
LLM Provider — Google Gemini
==============================
Gemini implementation of the LLMProvider interface.

Team Owner: AI / LLM Team
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL
from layers.generation.base import LLMProvider


class GeminiLLMProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(
        self,
        model_name: str = GEMINI_CHAT_MODEL,
        api_key: str = GEMINI_API_KEY,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._configured = False

    def _ensure_configured(self) -> None:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set")
        if not self._configured:
            genai.configure(api_key=self._api_key)
            self._configured = True

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        chat_history: list[dict] | None = None,
    ) -> str:
        self._ensure_configured()
        model = genai.GenerativeModel(
            self._model_name,
            system_instruction=system_prompt if system_prompt else None,
        )
        history: list[dict] = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
        chat = model.start_chat(history=history)
        response = chat.send_message(user_prompt)
        return response.text

    def generate_simple(self, prompt: str) -> str:
        self._ensure_configured()
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content(prompt)
        return response.text
