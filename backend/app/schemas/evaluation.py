from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvaluationRunRequest(BaseModel):
    name: Optional[str] = "Experiment Run"
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 100
    retrieval_strategy: Optional[str] = "hybrid"  # "dense", "sparse", "hybrid"
    top_k: Optional[int] = 5
    rerank: Optional[bool] = True
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    dataset_path: Optional[str] = None

class EvaluationMetricResult(BaseModel):
    metric_name: str
    metric_value: float
    sample_count: int
    details: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}

class EvaluationExperimentResponse(BaseModel):
    id: str
    name: str
    configuration: Dict[str, Any]
    embedding_model: str
    llm_model: str
    status: str
    created_at: datetime
    results: List[EvaluationMetricResult] = []

    model_config = {"from_attributes": True}

class ExperimentComparisonResponse(BaseModel):
    experiments: List[EvaluationExperimentResponse]
    metrics_summary: Dict[str, Dict[str, float]]  # metric_name -> {experiment_id: value}

