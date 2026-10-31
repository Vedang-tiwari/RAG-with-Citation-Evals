import hashlib
import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingestion.parser import DocumentParser
from backend.app.ingestion.cleaner import TextCleaner
from backend.app.ingestion.chunker import ConfigurableChunker
from backend.app.embeddings.embedder import embedder
from backend.app.retrieval.vector_search import vector_engine
from backend.app.retrieval.bm25_search import bm25_engine
from backend.app.database.repository import DocumentRepository, ChunkRepository

class IngestionPipeline:
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @classmethod
    def process_document(
        cls,
        db: Session,
        doc_id: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processes an uploaded document:
        1. Extract text page-by-page.
        2. Clean text.
        3. Split into overlapping chunks with page metadata.
        4. Save chunks in relational DB.
        5. Generate embeddings and upsert into Qdrant.
        6. Add to BM25 index.
        """
        doc = DocumentRepository.get_by_id(db, doc_id)
        if not doc:
            raise ValueError(f"Document with id {doc_id} not found.")

        DocumentRepository.update_status(db, doc_id, "processing")

        try:
            # 1. Parse text
            raw_pages = DocumentParser.parse_file(doc.storage_path, doc.file_type)
            if not raw_pages:
                raise ValueError("No extractable text found in document.")

            # 2. Clean text
            cleaned_pages = [(page_num, TextCleaner.clean(text)) for page_num, text in raw_pages]

            # 3. Chunk text
            c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
            c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
            chunker = ConfigurableChunker(chunk_size=c_size, chunk_overlap=c_overlap)
            chunks_data = chunker.split_text_into_chunks(doc_id=doc.id, pages_content=cleaned_pages)

            if not chunks_data:
                raise ValueError("Chunking resulted in 0 valid chunks.")

            # 4. Save chunks in DB (clean previous chunks if re-indexing)
            ChunkRepository.delete_by_document(db, doc.id)
            ChunkRepository.bulk_create(db, chunks_data)

            # 5. Generate embeddings and upsert to Qdrant
            texts = [c["content"] for c in chunks_data]
            vectors = embedder.embed_texts(texts)
            vector_engine.upsert_chunks(chunks=chunks_data, vectors=vectors, filename=doc.filename)

            # 6. Add chunks to BM25 engine
            bm25_items = [
                {
                    "chunk_id": c["id"],
                    "document_id": doc.id,
                    "document_name": doc.filename,
                    "page_number": c.get("page_number"),
                    "content": c["content"]
                }
                for c in chunks_data
            ]
            bm25_engine.add_chunks(bm25_items)

            # 7. Update status to indexed
            DocumentRepository.update_status(db, doc_id, "indexed", chunk_count=len(chunks_data))
            logger.info(f"Successfully processed and indexed document {doc.filename} ({len(chunks_data)} chunks)")

            return {
                "document_id": doc.id,
                "filename": doc.filename,
                "status": "indexed",
                "chunk_count": len(chunks_data)
            }

        except Exception as e:
            logger.error(f"Failed to process document {doc.filename}: {e}", exc_info=True)
            DocumentRepository.update_status(db, doc_id, "error", error=str(e))
            raise e

    @classmethod
    def delete_document(cls, db: Session, doc_id: str) -> bool:
        doc = DocumentRepository.get_by_id(db, doc_id)
        if not doc:
            return False

        # Remove from vector db & BM25
        vector_engine.delete_document(doc_id)
        bm25_engine.remove_document(doc_id)

        # Remove file from disk
        if os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except Exception as e:
                logger.warning(f"Failed to remove file from disk: {e}")

        # Delete from DB
        return DocumentRepository.delete(db, doc_id)

    @classmethod
    def sync_bm25_from_db(cls, db: Session):
        """
        Rebuilds BM25 index from all indexed chunks in DB.
        """
        from backend.app.database.models import Chunk, Document
        records = (
            db.query(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .filter(Document.status == "indexed")
            .all()
        )
        items = [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_name": filename,
                "page_number": chunk.page_number,
                "content": chunk.content
            }
            for chunk, filename in records
        ]
        bm25_engine.index_chunks(items)

