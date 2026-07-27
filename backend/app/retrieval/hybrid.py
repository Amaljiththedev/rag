from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.embeddings import EmbeddingWrapper
from app.retrieval.vector_store import VectorStoreClient
from app.retrieval.keyword_store import KeywordStoreClient

class HybridRetriever:
    """Reciprocal Rank Fusion (RRF) of Dense Vector + Keyword Search."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.embedder = EmbeddingWrapper()
        self.vector_store = VectorStoreClient(db_session)
        self.keyword_store = KeywordStoreClient(db_session)

    async def search(self, query: str, top_k: int = 5, k_rrf: int = 60) -> List[Dict[str, Any]]:
        query_vector = await self.embedder.embed_query(query)

        vector_results = await self.vector_store.similarity_search(query_vector, top_k=top_k * 2)
        keyword_results = await self.keyword_store.keyword_search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        # Process vector results
        for rank, res in enumerate(vector_results):
            cid = res["chunk_id"]
            chunks_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank + 1))

        # Process keyword results
        for rank, res in enumerate(keyword_results):
            cid = res["chunk_id"]
            chunks_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank + 1))

        # Sort by RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

        fused_results = []
        for cid in sorted_ids:
            item = chunks_map[cid]
            item["score"] = rrf_scores[cid]
            fused_results.append(item)

        return fused_results
