from typing import List

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.ingestion.pipeline import delete_document_set, list_document_sets
from app.schemas.session import WorkspaceSummary

router = APIRouter()


@router.get("/workspaces", response_model=List[WorkspaceSummary])
async def get_workspaces():
    """Indexed documents, newest first. Backs the sidebar."""
    rows = await run_in_threadpool(list_document_sets)
    return [WorkspaceSummary(**row) for row in rows]


@router.delete("/workspaces/{document_set_id}")
async def remove_workspace(document_set_id: str):
    """Delete a document and every chunk indexed from it."""
    deleted = await run_in_threadpool(delete_document_set, document_set_id)
    if deleted == 0:
        raise HTTPException(
            status_code=404, detail=f"No workspace found for '{document_set_id}'."
        )
    return {"document_set_id": document_set_id, "chunks_deleted": deleted}
