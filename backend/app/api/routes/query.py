from fastapi import APIRouter, HTTPException

from app.generation.generate import generate_answer
from app.ingestion.pipeline import count_chunks
from app.schemas.session import SessionQueryRequest, SessionQueryResponse

router = APIRouter()


@router.post("/query", response_model=SessionQueryResponse)
async def query_documents(request: SessionQueryRequest):
    """Answer a question using only the chunks in the caller's document set."""
    n_chunks = count_chunks(request.document_set_id)
    if n_chunks == 0:
        print(f"[query] rejected unknown/empty set {request.document_set_id}")
        raise HTTPException(
            status_code=404,
            detail=(
                f"No documents found for document_set_id '{request.document_set_id}'. "
                "Upload a file via POST /upload first."
            ),
        )

    print(f"[query] set {request.document_set_id} has {n_chunks} chunks")

    try:
        result = generate_answer(
            request.question,
            request.document_set_id,
            top_k=request.top_k,
        )
    except Exception as e:
        print(f"[query] generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    return SessionQueryResponse(**result)
