from typing import List

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_set_id: str
    filename: str
    chunks_created: int


class SessionQueryRequest(BaseModel):
    document_set_id: str = Field(..., description="Set returned by POST /upload")
    question: str = Field(..., description="Question to answer from that set only")
    top_k: int = Field(default=5, ge=1, le=20)


class SessionSource(BaseModel):
    n: int
    chunk_id: str
    section: str


class SessionQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SessionSource] = []
