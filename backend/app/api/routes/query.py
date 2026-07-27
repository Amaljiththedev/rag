from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.query import QueryRequest, QueryResponse, SourceCitation
from app.graph.rag_graph import RAGGraphPipeline

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """POST /query - Main RAG endpoint executing retrieval and generation via LangGraph."""
    pipeline = RAGGraphPipeline(db)
    graph = pipeline.build_graph()

    initial_state = {
        "question": request.question,
        "chunks": [],
        "answer": "",
        "confidence_score": 0.0,
        "refused": False
    }

    final_state = await graph.ainvoke(initial_state)

    sources = [
        SourceCitation(
            document_id=c.get("document_id", ""),
            filename=c.get("filename", ""),
            chunk_index=c.get("chunk_index", 0),
            content=c.get("content", ""),
            score=c.get("score", 0.0)
        )
        for c in final_state.get("chunks", [])
    ]

    return QueryResponse(
        question=final_state["question"],
        answer=final_state["answer"],
        refused=final_state["refused"],
        confidence_score=final_state["confidence_score"],
        sources=sources
    )
