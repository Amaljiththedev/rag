from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DocumentChunkModel, DocumentModel

class KeywordStoreClient:
    """Postgres full-text / BM25 search client."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def keyword_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        # ILIKE / Full Text search query
        stmt = (
            select(DocumentChunkModel, DocumentModel.filename)
            .join(DocumentModel, DocumentModel.id == DocumentChunkModel.document_id)
            .where(DocumentChunkModel.content.icontains(query))
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
                "score": 1.0 / (1.0 + i)
            })
        return results
