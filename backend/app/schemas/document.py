from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class DocumentIngestResponse(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    status: str

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    created_at: datetime
