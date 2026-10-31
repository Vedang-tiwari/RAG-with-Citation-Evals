from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.evaluation.reports import ExperimentReporter

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.get("/compare")
def compare_experiments(
    experiment_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    return ExperimentReporter.compare_experiments(db=db, experiment_ids=experiment_ids)

