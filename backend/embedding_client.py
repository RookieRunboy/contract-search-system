"""HTTP client for remote embedding service."""

from __future__ import annotations

import os
from typing import Iterable, List, Sequence, Union

import requests


class RemoteEmbeddingClient:
    """Small wrapper to fetch embeddings from the remote bge-m3 service."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "bge-m3",
        endpoint: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        # Keep the same API key source as metadata extraction.
        self.api_key = api_key or os.getenv("CONTRACT_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "CONTRACT_API_KEY (or DEEPSEEK_API_KEY) is required for remote embeddings"
            )
        self.endpoint = endpoint or os.getenv("CONTRACT_EMBEDDING_URL") or "http://model.aicc.chinasoftinc.com/v1/embeddings"
        self.model = model
        self.timeout = timeout

    def embed(self, texts: Union[str, Sequence[str]]) -> List[List[float]]:
        if isinstance(texts, str):
            payload_inputs: List[str] = [texts]
        else:
            payload_inputs = list(texts)
        if not payload_inputs:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "input": payload_inputs,
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=body,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        embeddings = data.get("data")
        if not isinstance(embeddings, Iterable):
            raise ValueError(f"Unexpected embedding response format: {data}")

        results: List[List[float]] = []
        for item in embeddings:
            embedding = item.get("embedding") if isinstance(item, dict) else None
            if not isinstance(embedding, list):
                raise ValueError(f"Invalid embedding entry: {item}")
            results.append(embedding)
        return results
