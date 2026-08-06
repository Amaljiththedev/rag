import os
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.ingestion.loaders import LOADERS
from app.ingestion.pipeline import ingest_file
from app.schemas.session import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_set_id: str | None = Form(default=None),
):
    """Upload a PDF or TXT, ingest it, and return the document_set_id to query it with."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in LOADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(LOADERS))}",
        )

    tmp_dir = tempfile.mkdtemp(prefix="rag_upload_")
    tmp_path = os.path.join(tmp_dir, os.path.basename(file.filename))
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        print(f"[upload] saved {file.filename} to {tmp_path}")

        result = ingest_file(tmp_path, document_set_id)
    except ValueError as e:
        print(f"[upload] rejected {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[upload] failed to ingest {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return UploadResponse(**result)
