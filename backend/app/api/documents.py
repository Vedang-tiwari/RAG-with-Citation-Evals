import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.repository import DocumentRepository, ChunkRepository
from backend.app.schemas.document import DocumentResponse, DocumentDetailResponse, ReindexRequest
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save uploaded file to temp/upload location
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(temp_path)
    file_hash = IngestionPipeline.calculate_file_hash(temp_path)

    # Check for duplicate document
    existing = DocumentRepository.get_by_hash(db, file_hash)
    if existing:
        if os.path.exists(temp_path) and temp_path != existing.storage_path:
            os.remove(temp_path)
        return existing

    # Create document record
    doc = DocumentRepository.create(
        db=db,
        filename=file.filename,
        file_hash=file_hash,
        file_type=ext,
        file_size=file_size,
        storage_path=temp_path
    )

    # Process and index immediately
    try:
        IngestionPipeline.process_document(db=db, doc_id=doc.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

    return doc


@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return DocumentRepository.list_all(db)


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = DocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = ChunkRepository.get_by_document(db, doc_id)
    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_hash=doc.file_hash,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=chunks
    )


@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    success = IngestionPipeline.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "id": doc_id}


@router.post("/{doc_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    doc_id: str,
    payload: Optional[ReindexRequest] = None,
    db: Session = Depends(get_db)
):
    doc = DocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    c_size = payload.chunk_size if payload else None
    c_overlap = payload.chunk_overlap if payload else None

    try:
        IngestionPipeline.process_document(
            db=db,
            doc_id=doc_id,
            chunk_size=c_size,
            chunk_overlap=c_overlap
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")

    return doc

