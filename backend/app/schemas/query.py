from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SourceCitation(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float

class QueryRequest(BaseModel):
    question: str = Field(..., description="User prompt or question")
    top_k: Optional[int] = Field(default=5, description="Number of context chunks to retrieve")

class QueryResponse(BaseModel):
    question: str
    answer: str
    refused: bool = False
    confidence_score: float
    sources: List[SourceCitation] = []
