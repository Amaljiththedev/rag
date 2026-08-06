import asyncio
import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.ingestion.loaders import LOADERS
from app.ingestion.pipeline import ingest_file
from app.progress import make_emitter
from app.schemas.session import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_set_id: Optional[str] = Form(default=None),
    channel: Optional[str] = Form(default=None),
):
    """Upload a PDF or TXT, ingest it, and return the document_set_id to query it with.

    If `channel` matches an open /ws/progress/{channel} socket, stage events are
    streamed to it while the file is processed.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in LOADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(LOADERS))}",
        )

    emit = make_emitter(channel, asyncio.get_running_loop())

    tmp_dir = tempfile.mkdtemp(prefix="rag_upload_")
    tmp_path = os.path.join(tmp_dir, os.path.basename(file.filename))
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        emit("uploaded", f"Received {file.filename}", filename=file.filename)

        # Ingestion is CPU-bound (embedding) and blocking (psycopg2). Off the
        # event loop, or progress events can't flush while it runs.
        result = await run_in_threadpool(ingest_file, tmp_path, document_set_id, emit)
    except ValueError as e:
        emit("error", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        emit("error", f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return UploadResponse(**result)
