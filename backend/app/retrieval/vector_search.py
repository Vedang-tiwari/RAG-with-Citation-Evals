import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.core.config import settings
from backend.app.core.logging import logger

class VectorSearchEngine:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self._init_client()

    def _init_client(self):
        try:
            if settings.QDRANT_URL:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )
            elif settings.QDRANT_STORAGE_PATH and settings.QDRANT_STORAGE_PATH != ":memory:":
                os.makedirs(settings.QDRANT_STORAGE_PATH, exist_ok=True)
                lock_file = os.path.join(settings.QDRANT_STORAGE_PATH, ".lock")
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                    except Exception:
                        pass
                try:
                    self.client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)
                except Exception as path_err:
                    logger.warning(f"Failed to lock Qdrant storage path ({path_err}). Using in-memory fallback.")
                    self.client = QdrantClient(":memory:")
            else:
                self.client = QdrantClient(":memory:")
        except Exception as e:
            logger.warning(f"Error initializing Qdrant client with storage path ({e}). Using in-memory fallback.")
            self.client = QdrantClient(":memory:")

    def ensure_collection(self, vector_size: int = 384):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error checking/creating collection: {e}")

    def upsert_chunks(self, chunks: List[Dict[str, Any]], vectors: List[List[float]], filename: str):
        if not chunks:
            return
        self.ensure_collection(vector_size=len(vectors[0]))

        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = abs(hash(chunk["id"])) % (10**12)  # numeric point id for Qdrant compatibility
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk["id"],
                        "document_id": chunk["document_id"],
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk.get("page_number"),
                        "content": chunk["content"],
                        "filename": filename
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} chunks into Qdrant collection {self.collection_name}")

    def search(self, query_vector: List[float], top_k: int = 10, doc_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        self.ensure_collection(vector_size=len(query_vector))
        query_filter = None
        if doc_id_filter:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=doc_id_filter)
                    )
                ]
            )

        try:
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
                results = res.points
            else:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )

            hits = []
            for hit in results:
                payload = hit.payload or {}
                hits.append({
                    "chunk_id": payload.get("chunk_id", ""),
                    "document_id": payload.get("document_id", ""),
                    "document_name": payload.get("filename", ""),
                    "page_number": payload.get("page_number"),
                    "content": payload.get("content", ""),
                    "similarity_score": float(hit.score)
                })
            return hits
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def delete_document(self, document_id: str):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted vector chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting chunks from Qdrant: {e}")

vector_engine = VectorSearchEngine()

