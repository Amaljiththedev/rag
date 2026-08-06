from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_set_id: str
    filename: str
    chunks_created: int
    page_count: int = 0
    section_count: int = 0


class WorkspaceSummary(BaseModel):
    """A row in the sidebar's document list."""

    document_set_id: str
    filename: str
    file_type: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: Optional[datetime] = None


class SessionQueryRequest(BaseModel):
    document_set_id: str = Field(..., description="Set returned by POST /upload")
    question: str = Field(..., description="Question to answer from that set only")
    top_k: int = Field(default=5, ge=1, le=20)
    channel: Optional[str] = Field(default=None, description="Progress WebSocket channel id")


class Evidence(BaseModel):
    """Where a passage came from — shown instead of an opaque chunk id."""

    n: int
    document: str
    section: Optional[str] = None
    page_label: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    chunk_id: str


class SessionQueryResponse(BaseModel):
    question: str
    answer: str
    refused: bool = False
    evidence: List[Evidence] = []
