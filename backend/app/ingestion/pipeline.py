import os
import uuid
from typing import Any, Callable, Dict, Optional

import psycopg2

from app.ingestion.loaders import load_file
from app.ingestion.chunking import chunk_document
from app.retrieval.search import embed_text, DB_CONFIG

INSERT_CHUNK_SQL = """
    INSERT INTO chunks
        (chunk_id, source_file, company, section, chunk_index, content, embedding, document_set_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chunk_id) DO UPDATE SET
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        document_set_id = EXCLUDED.document_set_id;
"""


def _noop_progress(stage: str, message: str, **extra: Any) -> None:
    print(f"[{stage}] {message}")


def ingest_file(
    filepath: str,
    document_set_id: Optional[str] = None,
    on_progress: Optional[Callable[..., None]] = None,
) -> Dict[str, Any]:
    """Load, chunk, embed and store a file, tagging every chunk with a document_set_id.

    Returns {"document_set_id", "filename", "chunks_created"}. The caller needs the
    document_set_id to query this upload later. on_progress(stage, message, **extra)
    is called at each stage so callers can stream progress to a UI.
    """
    progress = on_progress or _noop_progress

    if document_set_id is None:
        document_set_id = str(uuid.uuid4())
        print(f"[ingest] generated new document_set_id: {document_set_id}")
    else:
        print(f"[ingest] using provided document_set_id: {document_set_id}")

    filename = os.path.basename(filepath)

    progress("reading", f"Reading {filename}", document_set_id=document_set_id)
    text = load_file(filepath)

    progress("chunking", "Splitting document into chunks")
    chunks = chunk_document(text, source_file=filename, company="User Upload")
    if not chunks:
        raise ValueError(f"{filename} produced no chunks — nothing to ingest.")

    total = len(chunks)
    progress("chunking", f"Split into {total} chunks", total_chunks=total)

    for i, chunk in enumerate(chunks, start=1):
        chunk["embedding"] = embed_text(chunk["text"])
        if i % 5 == 0 or i == total:
            progress(
                "embedding",
                f"Embedding chunk {i} of {total}",
                current=i,
                total_chunks=total,
                percent=round(i / total * 100),
            )

    progress("storing", f"Saving {total} chunks to the database", total_chunks=total)
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
        progress("error", f"Failed saving chunks for {filename}: {e}")
        raise
    finally:
        conn.close()

    progress(
        "done",
        f"Ready — {total} chunks indexed",
        document_set_id=document_set_id,
        filename=filename,
        total_chunks=total,
    )
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
