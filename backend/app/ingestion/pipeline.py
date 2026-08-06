import os
import uuid
from typing import Any, Callable, Dict, Optional

import psycopg2

from app.ingestion.loaders import load_file, page_count
from app.ingestion.chunking import chunk_document
from app.retrieval.search import embed_text, DB_CONFIG

INSERT_CHUNK_SQL = """
    INSERT INTO chunks
        (chunk_id, source_file, company, section, chunk_index, content, embedding,
         document_set_id, page_start, page_end)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chunk_id) DO UPDATE SET
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        document_set_id = EXCLUDED.document_set_id,
        section = EXCLUDED.section,
        page_start = EXCLUDED.page_start,
        page_end = EXCLUDED.page_end;
"""

UPSERT_SET_SQL = """
    INSERT INTO document_sets
        (document_set_id, filename, file_type, page_count, chunk_count)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (document_set_id) DO UPDATE SET
        filename = EXCLUDED.filename,
        page_count = EXCLUDED.page_count,
        chunk_count = EXCLUDED.chunk_count;
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
    pages = load_file(filepath)
    n_pages = page_count(pages)
    progress(
        "reading",
        f"Read {n_pages} page{'' if n_pages == 1 else 's'}",
        page_count=n_pages,
    )

    progress("chunking", "Finding sections")
    chunks = chunk_document(pages, source_file=filename, company="User Upload")
    if not chunks:
        raise ValueError(f"{filename} produced no chunks — nothing to ingest.")

    total = len(chunks)
    n_sections = len({c["section"] for c in chunks if c["section"]})
    progress(
        "chunking",
        f"{total} passages across {n_sections} section{'' if n_sections == 1 else 's'}"
        if n_sections
        else f"{total} passages",
        total_chunks=total,
        sections=n_sections,
    )

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
                            chunk["page_start"],
                            chunk["page_end"],
                        ),
                    )
                cur.execute(
                    UPSERT_SET_SQL,
                    (
                        document_set_id,
                        filename,
                        os.path.splitext(filename)[1].lstrip(".").lower(),
                        n_pages,
                        total,
                    ),
                )
    except Exception as e:
        progress("error", f"Failed saving chunks for {filename}: {e}")
        raise
    finally:
        conn.close()

    progress(
        "done",
        "Ready",
        document_set_id=document_set_id,
        filename=filename,
        total_chunks=total,
        page_count=n_pages,
    )
    return {
        "document_set_id": document_set_id,
        "filename": filename,
        "chunks_created": total,
        "page_count": n_pages,
        "section_count": n_sections,
    }


def list_document_sets() -> list:
    """Every indexed document, newest first — drives the sidebar."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT document_set_id, filename, file_type, page_count,
                       chunk_count, created_at
                FROM document_sets
                ORDER BY created_at DESC;
                """
            )
            return [
                {
                    "document_set_id": r[0],
                    "filename": r[1],
                    "file_type": r[2],
                    "page_count": r[3],
                    "chunk_count": r[4],
                    "created_at": r[5],
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()


def delete_document_set(document_set_id: str) -> int:
    """Remove a document and its chunks. Returns chunks deleted."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chunks WHERE document_set_id = %s;", (document_set_id,)
                )
                deleted = cur.rowcount
                cur.execute(
                    "DELETE FROM document_sets WHERE document_set_id = %s;",
                    (document_set_id,),
                )
        return deleted
    finally:
        conn.close()


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
