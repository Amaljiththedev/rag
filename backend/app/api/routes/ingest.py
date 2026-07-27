from fastapi import APIRouter, UploadFile, File, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.document import DocumentIngestResponse
from app.ingestion.pipeline import IngestionPipeline

router = APIRouter()

@router.post("/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """POST /ingest - Upload and trigger document ingestion pipeline."""
    content = await file.read()
    pipeline = IngestionPipeline(db)
    result = await pipeline.ingest_bytes(content, file.filename)
    return DocumentIngestResponse(**result)
