import asyncio

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.generation.generate import generate_answer
from app.ingestion.pipeline import count_chunks
from app.progress import make_emitter
from app.schemas.session import SessionQueryRequest, SessionQueryResponse

router = APIRouter()


@router.post("/query", response_model=SessionQueryResponse)
async def query_documents(request: SessionQueryRequest):
    """Answer a question using only the chunks in the caller's document set."""
    emit = make_emitter(request.channel, asyncio.get_running_loop())

    n_chunks = await run_in_threadpool(count_chunks, request.document_set_id)
    if n_chunks == 0:
        emit("error", "That document set is empty or unknown.")
        raise HTTPException(
            status_code=404,
            detail=(
                f"No documents found for document_set_id '{request.document_set_id}'. "
                "Upload a file via POST /upload first."
            ),
        )

    try:
        emit("retrieving", "Finding evidence")
        result = await run_in_threadpool(
            generate_answer,
            request.question,
            request.document_set_id,
            request.top_k,
            emit,
        )
    except Exception as e:
        emit("error", f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    emit("done", "Answer ready")
    return SessionQueryResponse(**result)
