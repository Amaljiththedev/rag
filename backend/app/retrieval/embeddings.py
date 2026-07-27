from typing import List
from langchain_openai import OpenAIEmbeddings
from app.config import settings

class EmbeddingWrapper:
    """Embedding model wrapper for OpenAI / custom models."""

    def __init__(self):
        self.client = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY or "placeholder"
        )

    async def embed_query(self, query: str) -> List[float]:
        try:
            return await self.client.aembed_query(query)
        except Exception:
            # Fallback zero vector for offline/testing mode
            return [0.0] * 1536

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return await self.client.aembed_documents(texts)
        except Exception:
            return [[0.0] * 1536 for _ in texts]
