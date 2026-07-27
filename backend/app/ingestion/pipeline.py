import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ingestion.loaders import DocumentLoader
from app.ingestion.chunking import TextChunker
from app.retrieval.embeddings import EmbeddingWrapper
from app.db.models import DocumentModel, DocumentChunkModel

class IngestionPipeline:
    """Orchestrates: load -> chunk -> embed -> store."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.embedder = EmbeddingWrapper()

    async def ingest_bytes(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        if filename.endswith(".pdf"):
            raw_docs = self.loader.load_pdf(file_bytes, filename)
        else:
            raw_docs = self.loader.load_text(file_bytes.decode("utf-8", errors="ignore"), filename)

        chunks = self.chunker.split_documents(raw_docs)
        texts = [c["content"] for c in chunks]
        embeddings = await self.embedder.embed_documents(texts)

        doc_record = DocumentModel(
            id=str(uuid.uuid4()),
            filename=filename,
            file_type=filename.split(".")[-1]
        )
        self.db.add(doc_record)

        for i, chunk in enumerate(chunks):
            chunk_record = DocumentChunkModel(
                id=str(uuid.uuid4()),
                document_id=doc_record.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=embeddings[i],
                metadata_json=chunk["metadata"]
            )
            self.db.add(chunk_record)

        await self.db.commit()

        return {
            "document_id": doc_record.id,
            "filename": filename,
            "num_chunks": len(chunks),
            "status": "completed"
        }
