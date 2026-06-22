from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class SinglePredictRequest(BaseModel):
    features: dict[str, float]


class SinglePredictResponse(BaseModel):
    churn_probability: float
    churn_prediction: int


class BatchPredictResponse(BaseModel):
    count: int
    predictions: list[dict[str, float]]


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    version: str
    trained_at: str
    val_logloss: float
    val_auc: float
    num_features: int
    num_trees: int
    mlflow_run_id: Optional[str] = None


class FeatureImpact(BaseModel):
    feature: str
    impact: float


class ExplainRequest(BaseModel):
    features: dict[str, float]
    top_n: int = 10


class ExplainResponse(BaseModel):
    probability: float
    churn_prediction: int
    top_features: list[FeatureImpact]