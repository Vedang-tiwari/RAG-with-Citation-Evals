import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG with Citations + Evals"
    API_V1_STR: str = "/api"
    
    # Storage & Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rag_citations.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    QDRANT_STORAGE_PATH: Optional[str] = os.getenv("QDRANT_STORAGE_PATH", "./data/qdrant")
    QDRANT_URL: Optional[str] = os.getenv("QDRANT_URL", None)
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "rag_documents")
    
    # Models & Defaults
    DEFAULT_EMBEDDING_MODEL: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    DEFAULT_RERANKER_MODEL: str = os.getenv("DEFAULT_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "100"))
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "10"))
    DEFAULT_FINAL_TOP_K: int = int(os.getenv("DEFAULT_FINAL_TOP_K", "4"))
    
    # LLM Provider Configuration
    # Options: "gemini", "openai", "groq", "mock"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # Hybrid Search Weights
    DENSE_WEIGHT: float = 0.6
    SPARSE_WEIGHT: float = 0.4
    RERANKER_ENABLED: bool = True
    
    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()

