from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.repository import EvaluationRepository
from backend.app.schemas.evaluation import (
    EvaluationRunRequest, EvaluationExperimentResponse
)
from backend.app.evaluation.runner import EvaluationRunner

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/run")
def run_evaluation(
    payload: EvaluationRunRequest,
    db: Session = Depends(get_db)
):
    try:
        report = EvaluationRunner.run_experiment(
            db=db,
            name=payload.name or "RAG Benchmark",
            chunk_size=payload.chunk_size or 500,
            chunk_overlap=payload.chunk_overlap or 100,
            retrieval_strategy=payload.retrieval_strategy or "hybrid",
            top_k=payload.top_k or 5,
            rerank=payload.rerank if payload.rerank is not None else True,
            embedding_model=payload.embedding_model,
            llm_model=payload.llm_model,
            dataset_path=payload.dataset_path
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/results", response_model=List[EvaluationExperimentResponse])
def get_evaluation_results(db: Session = Depends(get_db)):
    return EvaluationRepository.list_experiments(db)


@router.get("/{experiment_id}", response_model=EvaluationExperimentResponse)
def get_experiment_details(experiment_id: str, db: Session = Depends(get_db)):
    exp = EvaluationRepository.get_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

