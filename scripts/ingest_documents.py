#!/usr/bin/env python
import os
import sys
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal, init_db
from backend.app.database.repository import DocumentRepository
from backend.app.ingestion.pipeline import IngestionPipeline

def main():
    parser = argparse.ArgumentParser(description="Ingest documents into RAG with Citations knowledge base")
    parser.add_argument("--path", required=True, help="Path to document file or folder")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size in words/tokens")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap in words/tokens")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Error: Path does not exist: {target_path}")
        sys.exit(1)

    files_to_process = []
    if os.path.isfile(target_path):
        files_to_process.append(target_path)
    else:
        for root, _, files in os.walk(target_path):
            for f in files:
                ext = f.split(".")[-1].lower()
                if ext in ["pdf", "docx", "doc", "txt", "md"]:
                    files_to_process.append(os.path.join(root, f))

    print(f"Found {len(files_to_process)} document(s) to process.")

    for fpath in files_to_process:
        filename = os.path.basename(fpath)
        ext = filename.split(".")[-1].lower()
        file_size = os.path.getsize(fpath)
        file_hash = IngestionPipeline.calculate_file_hash(fpath)

        existing = DocumentRepository.get_by_hash(db, file_hash)
        if existing:
            print(f"[SKIP] Document already indexed: {filename} (ID: {existing.id})")
            continue

        print(f"[INDEXING] {filename}...")
        doc = DocumentRepository.create(
            db=db,
            filename=filename,
            file_hash=file_hash,
            file_type=ext,
            file_size=file_size,
            storage_path=fpath
        )

        try:
            res = IngestionPipeline.process_document(
                db=db,
                doc_id=doc.id,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            print(f"[SUCCESS] {filename} indexed successfully ({res['chunk_count']} chunks).")
        except Exception as e:
            print(f"[ERROR] Failed to index {filename}: {e}")

    db.close()
    print("Ingestion completed.")

if __name__ == "__main__":
    main()

