from __future__ import annotations

"""
EMBEDDING LAYER — AWS Bedrock Backend
========================================
AWS Bedrock Titan Embeddings implementation.
Requires boto3 and valid AWS credentials.

Team Owner: ML / Embeddings Team
"""

from layers.embedding.base import EmbeddingProvider
from config import BEDROCK_EMBED_MODEL, AWS_REGION


class BedrockEmbeddingProvider(EmbeddingProvider):
    """AWS Bedrock (Titan Embeddings) provider."""

    def __init__(
        self,
        model_id: str = BEDROCK_EMBED_MODEL,
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

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import json

        client = self._get_client()
        embeddings: list[list[float]] = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = client.invoke_model(
                modelId=self._model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
