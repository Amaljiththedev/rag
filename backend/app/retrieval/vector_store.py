from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DocumentChunkModel, DocumentModel

class VectorStoreClient:
    """pgvector similarity search client."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def similarity_search(self, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        stmt = (
            select(DocumentChunkModel, DocumentModel.filename)
            .join(DocumentModel, DocumentModel.id == DocumentChunkModel.document_id)
            .order_by(DocumentChunkModel.embedding.l2_distance(query_vector))
            .limit(top_k)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        results = []
        for i, (chunk, filename) in enumerate(rows):
            results.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "score": 1.0 / (1.0 + i)  # Simulated vector score based on rank
            })
        return results
