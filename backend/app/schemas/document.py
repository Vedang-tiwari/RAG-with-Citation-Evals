from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_hash: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class DocumentDetailResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []

class ReindexRequest(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

