from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import init_db, SessionLocal
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.api import documents, chat, evaluation, experiments

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        db = SessionLocal()
        try:
            IngestionPipeline.sync_bm25_from_db(db)
        except Exception as e:
            logger.warning(f"Initial BM25 sync notice: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Startup error: {e}")
    
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A Citation-Grounded Retrieval-Augmented Generation System with Automated Evaluation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(evaluation.router, prefix=settings.API_V1_STR)
app.include_router(experiments.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": settings.DATABASE_URL.split("://")[0],
        "vector_db": "qdrant"
    }

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access API docs at /docs"
    }
