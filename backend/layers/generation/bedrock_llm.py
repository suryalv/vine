from __future__ import annotations

"""
LLM Provider — AWS Bedrock
============================
AWS Bedrock implementation (Claude, Titan, etc.)
Requires boto3 and valid AWS credentials.

Team Owner: AI / LLM Team
"""

from layers.generation.base import LLMProvider
from config import BEDROCK_CHAT_MODEL, AWS_REGION


class BedrockLLMProvider(LLMProvider):
    """AWS Bedrock LLM provider."""

    def __init__(
        self,
        model_id: str = BEDROCK_CHAT_MODEL,
        region: str = AWS_REGION,
    ):
        self._model_id = model_id
        self._region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "bedrock-runtime", region_name=self._region
            )
        return self._client

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        chat_history: list[dict] | None = None,
    ) -> str:
        import json

        client = self._get_client()

        messages: list[dict] = []
        if chat_history:
            for msg in chat_history:
                role = msg["role"] if msg["role"] in ("user", "assistant") else "user"
                messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        body: dict = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def generate_simple(self, prompt: str) -> str:
        return self.generate(user_prompt=prompt)
