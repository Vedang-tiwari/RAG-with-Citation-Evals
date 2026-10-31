from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database.models import (
    Document, Chunk, Conversation, Message, Citation,
    EvaluationExperiment, EvaluationResult
)

class DocumentRepository:
    @staticmethod
    def get_by_id(db: Session, doc_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == doc_id).first()

    @staticmethod
    def get_by_hash(db: Session, file_hash: str) -> Optional[Document]:
        return db.query(Document).filter(Document.file_hash == file_hash).first()

    @staticmethod
    def list_all(db: Session) -> List[Document]:
        return db.query(Document).order_by(Document.created_at.desc()).all()

    @staticmethod
    def create(db: Session, filename: str, file_hash: str, file_type: str, file_size: int, storage_path: str) -> Document:
        doc = Document(
            filename=filename,
            file_hash=file_hash,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def update_status(db: Session, doc_id: str, status: str, chunk_count: int = 0, error: Optional[str] = None) -> Optional[Document]:
        doc = DocumentRepository.get_by_id(db, doc_id)
        if doc:
            doc.status = status
            doc.chunk_count = chunk_count
            doc.error_message = error
            db.commit()
            db.refresh(doc)
        return doc

    @staticmethod
    def delete(db: Session, doc_id: str) -> bool:
        doc = DocumentRepository.get_by_id(db, doc_id)
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False


class ChunkRepository:
    @staticmethod
    def bulk_create(db: Session, chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
        chunk_objects = [
            Chunk(
                id=c["id"],
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                page_number=c.get("page_number"),
                token_count=c.get("token_count", 0),
                meta_info=c.get("meta_info")
            )
            for c in chunks_data
        ]
        db.add_all(chunk_objects)
        db.commit()
        return chunk_objects

    @staticmethod
    def get_by_id(db: Session, chunk_id: str) -> Optional[Chunk]:
        return db.query(Chunk).filter(Chunk.id == chunk_id).first()

    @staticmethod
    def get_by_document(db: Session, doc_id: str) -> List[Chunk]:
        return db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.chunk_index.asc()).all()

    @staticmethod
    def delete_by_document(db: Session, doc_id: str) -> int:
        deleted = db.query(Chunk).filter(Chunk.document_id == doc_id).delete()
        db.commit()
        return deleted


class ChatRepository:
    @staticmethod
    def get_or_create_conversation(db: Session, conv_id: Optional[str] = None, title: str = "New Chat") -> Conversation:
        if conv_id:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                return conv
        conv = Conversation(title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_conversation_history(db: Session, conv_id: str) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conv_id).first()

    @staticmethod
    def add_message(
        db: Session,
        conv_id: str,
        role: str,
        content: str,
        latency_ms: Optional[float] = None,
        tokens_used: int = 0,
        insufficient_evidence: bool = False
    ) -> Message:
        msg = Message(
            conversation_id=conv_id,
            role=role,
            content=content,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            insufficient_evidence=insufficient_evidence
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def add_citations(db: Session, message_id: str, citations: List[Dict[str, Any]]) -> List[Citation]:
        cit_objs = [
            Citation(
                message_id=message_id,
                chunk_id=c.get("chunk_id"),
                source_id=c["source_id"],
                quoted_text=c.get("quoted_text"),
                is_valid=c.get("is_valid", True),
                relevance_score=c.get("relevance_score")
            )
            for c in citations
        ]
        db.add_all(cit_objs)
        db.commit()
        return cit_objs


class EvaluationRepository:
    @staticmethod
    def create_experiment(
        db: Session,
        name: str,
        configuration: Dict[str, Any],
        embedding_model: str,
        llm_model: str
    ) -> EvaluationExperiment:
        exp = EvaluationExperiment(
            name=name,
            configuration=configuration,
            embedding_model=embedding_model,
            llm_model=llm_model,
            status="running"
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def complete_experiment(db: Session, exp_id: str, status: str = "completed") -> Optional[EvaluationExperiment]:
        exp = db.query(EvaluationExperiment).filter(EvaluationExperiment.id == exp_id).first()
        if exp:
            exp.status = status
            db.commit()
            db.refresh(exp)
        return exp

    @staticmethod
    def save_results(db: Session, exp_id: str, results: List[Dict[str, Any]]) -> List[EvaluationResult]:
        objs = [
            EvaluationResult(
                experiment_id=exp_id,
                metric_name=r["metric_name"],
                metric_value=r["metric_value"],
                sample_count=r.get("sample_count", 0),
                details=r.get("details")
            )
            for r in results
        ]
        db.add_all(objs)
        db.commit()
        return objs

    @staticmethod
    def list_experiments(db: Session) -> List[EvaluationExperiment]:
        return db.query(EvaluationExperiment).order_by(EvaluationExperiment.created_at.desc()).all()

    @staticmethod
    def get_experiment(db: Session, exp_id: str) -> Optional[EvaluationExperiment]:
        return db.query(EvaluationExperiment).filter(EvaluationExperiment.id == exp_id).first()

