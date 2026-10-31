from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CitationDetail(BaseModel):
    source_id: str  # e.g., "S1"
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    quoted_text: Optional[str] = None
    is_valid: bool = True
    confidence_score: Optional[float] = None

class RetrievedPassage(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    content: str
    similarity_score: float
    bm25_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: float

class ChatQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    top_k: Optional[int] = None
    retrieval_strategy: Optional[str] = "hybrid"  # "dense", "sparse", "hybrid"
    rerank: Optional[bool] = True
    temperature: Optional[float] = 0.2

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: List[CitationDetail] = []
    retrieved_passages: List[RetrievedPassage] = []
    insufficient_evidence: bool = False
    citation_precision: float = 1.0
    citation_coverage: float = 1.0
    latency_ms: float
    tokens_used: int = 0

class SourceEvidenceResponse(BaseModel):
    source_id: str
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    content: str
    quoted_text: Optional[str] = None
    is_valid: bool = True
    chunk_id: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    insufficient_evidence: bool = False
    latency_ms: Optional[float] = None
    citations: List[CitationDetail] = []
    created_at: datetime

    model_config = {"from_attributes": True}

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}

