from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.repository import ChatRepository, ChunkRepository, DocumentRepository
from backend.app.schemas.chat import (
    ChatQueryRequest, ChatResponse, ConversationResponse,
    SourceEvidenceResponse
)
from backend.app.generation.rag_pipeline import rag_engine

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query", response_model=ChatResponse)
def query_rag(
    payload: ChatQueryRequest,
    db: Session = Depends(get_db)
):
    try:
        response = rag_engine.answer_query(
            db=db,
            query=payload.query,
            conversation_id=payload.conversation_id,
            top_k=payload.top_k,
            retrieval_strategy=payload.retrieval_strategy,
            rerank=payload.rerank,
            temperature=payload.temperature or 0.2
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/history", response_model=List[ConversationResponse])
def get_chat_history(
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from backend.app.database.models import Conversation
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        return [conv] if conv else []
    return db.query(Conversation).order_by(Conversation.created_at.desc()).limit(20).all()


@router.get("/sources/{chunk_id}", response_model=SourceEvidenceResponse)
def get_source_evidence(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    chunk = ChunkRepository.get_by_id(db, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Source chunk not found")

    doc = DocumentRepository.get_by_id(db, chunk.document_id)
    return SourceEvidenceResponse(
        source_id="S",
        document_id=chunk.document_id,
        document_name=doc.filename if doc else "Unknown",
        page_number=chunk.page_number,
        content=chunk.content,
        quoted_text=None,
        is_valid=True,
        chunk_id=chunk.id
    )

