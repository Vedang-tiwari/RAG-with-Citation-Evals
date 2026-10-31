import os
import pytest
from backend.app.main import health_check, root
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.repository import DocumentRepository
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.generation.rag_pipeline import rag_engine
from backend.app.evaluation.runner import EvaluationRunner
from backend.app.evaluation.reports import ExperimentReporter

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert "service" in res
    assert res["vector_db"] == "qdrant"

def test_root_endpoint():
    res = root()
    assert "Welcome" in res["message"]

def test_document_ingestion_and_chat_query(db):
    os.makedirs("data/uploads", exist_ok=True)
    sample_file = "data/uploads/integration_sample.txt"
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("Multi-head attention allows the model to jointly attend to information from different representation subspaces. Self-attention relates different positions of a single sequence.")

    file_size = os.path.getsize(sample_file)
    file_hash = IngestionPipeline.calculate_file_hash(sample_file)

    # 1. Create document
    doc = DocumentRepository.create(
        db=db,
        filename="integration_sample.txt",
        file_hash=file_hash,
        file_type="txt",
        file_size=file_size,
        storage_path=sample_file
    )
    assert doc.id is not None
    assert doc.status == "pending"

    # 2. Ingest document
    res = IngestionPipeline.process_document(db=db, doc_id=doc.id, chunk_size=50, chunk_overlap=10)
    assert res["status"] == "indexed"
    assert res["chunk_count"] > 0

    # 3. Query RAG with citations
    chat_res = rag_engine.answer_query(
        db=db,
        query="What is multi-head attention?",
        retrieval_strategy="hybrid",
        rerank=True
    )
    assert "answer" in chat_res
    assert len(chat_res["answer"]) > 0
    assert len(chat_res["citations"]) > 0
    assert chat_res["citation_precision"] > 0.0

    # 4. Clean up document
    deleted = IngestionPipeline.delete_document(db=db, doc_id=doc.id)
    assert deleted is True

    if os.path.exists(sample_file):
        os.remove(sample_file)

def test_evaluation_experiment_run(db):
    report = EvaluationRunner.run_experiment(
        db=db,
        name="Integration Test Run",
        chunk_size=300,
        chunk_overlap=50,
        retrieval_strategy="hybrid",
        top_k=3,
        rerank=True
    )
    assert "experiment_id" in report
    assert "metrics" in report
    metrics = report["metrics"]
    assert "Precision@K" in metrics
    assert "Faithfulness" in metrics
    assert "Citation_Precision" in metrics

    # Test experiment comparison
    comparison = ExperimentReporter.compare_experiments(db=db, experiment_ids=[report["experiment_id"]])
    assert len(comparison["experiments"]) > 0
    assert "Precision@K" in comparison["metrics_summary"]
