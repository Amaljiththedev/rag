import os
import uuid
from typing import Dict, Any, Optional

import psycopg2
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.loaders import DocumentLoader, load_file
from app.ingestion.chunking import TextChunker, chunk_document
from app.retrieval.embeddings import EmbeddingWrapper
from app.retrieval.search import embed_text, DB_CONFIG
from app.db.models import DocumentModel, DocumentChunkModel

INSERT_CHUNK_SQL = """
    INSERT INTO chunks
        (chunk_id, source_file, company, section, chunk_index, content, embedding, document_set_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chunk_id) DO UPDATE SET
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        document_set_id = EXCLUDED.document_set_id;
"""


def ingest_file(filepath: str, document_set_id: Optional[str] = None) -> Dict[str, Any]:
    """Load, chunk, embed and store a file, tagging every chunk with a document_set_id.

    Returns {"document_set_id", "filename", "chunks_created"}. The caller needs the
    document_set_id to query this upload later.
    """
    if document_set_id is None:
        document_set_id = str(uuid.uuid4())
        print(f"[ingest] generated new document_set_id: {document_set_id}")
    else:
        print(f"[ingest] using provided document_set_id: {document_set_id}")

    filename = os.path.basename(filepath)

    text = load_file(filepath)

    chunks = chunk_document(text, source_file=filename, company="User Upload")
    if not chunks:
        raise ValueError(f"{filename} produced no chunks — nothing to ingest.")
    print(f"[ingest] split into {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, start=1):
        chunk["embedding"] = embed_text(chunk["text"])
        if i % 25 == 0 or i == len(chunks):
            print(f"[ingest] embedded {i}/{len(chunks)} chunks")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    # Namespace chunk_id by set so re-uploading the same filename
                    # in a different session doesn't collide on UNIQUE(chunk_id).
                    scoped_chunk_id = f"{document_set_id}__{chunk['chunk_id']}"
                    cur.execute(
                        INSERT_CHUNK_SQL,
                        (
                            scoped_chunk_id,
                            chunk["source_file"],
                            chunk["company"],
                            chunk["section"],
                            chunk["chunk_index"],
                            chunk["text"],
                            str(chunk["embedding"]),
                            document_set_id,
                        ),
                    )
    except Exception as e:
        print(f"[ingest] FAILED inserting chunks for {filename}: {e}")
        raise
    finally:
        conn.close()

    print(f"[ingest] stored {len(chunks)} chunks under document_set_id={document_set_id}")
    return {
        "document_set_id": document_set_id,
        "filename": filename,
        "chunks_created": len(chunks),
    }


def count_chunks(document_set_id: str) -> int:
    """How many chunks exist for a document set. Used to reject empty-set queries."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_set_id = %s;",
                (document_set_id,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


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
