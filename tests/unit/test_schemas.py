"""Unit tests for src/api/schemas.py — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    ExplainRequest,
    ExplainResponse,
    FeatureImpact,
    JobResponse,
    JobStatus,
    ModelInfo,
    SinglePredictRequest,
    SinglePredictResponse,
)

# ── JobStatus ─────────────────────────────────────────────


def test_job_status_has_all_four_values():
    assert set(JobStatus) == {"pending", "running", "done", "failed"}


def test_job_status_is_string_enum():
    assert JobStatus.done == "done"
    assert isinstance(JobStatus.done, str)


# ── JobResponse ───────────────────────────────────────────


def test_job_response_optional_fields_default_to_none():
    job = JobResponse(job_id="abc-123", status=JobStatus.pending)
    assert job.result is None
    assert job.error is None


def test_job_response_accepts_result_dict():
    job = JobResponse(
        job_id="abc-123",
        status=JobStatus.done,
        result={"val_auc": 0.98},
    )
    assert job.result["val_auc"] == 0.98


def test_job_response_accepts_error_string():
    job = JobResponse(
        job_id="abc-123",
        status=JobStatus.failed,
        error="something went wrong",
    )
    assert job.error == "something went wrong"


# ── SinglePredictRequest ──────────────────────────────────


def test_single_predict_request_requires_features():
    with pytest.raises(ValidationError):
        SinglePredictRequest()


def test_single_predict_request_accepts_empty_dict():
    req = SinglePredictRequest(features={})
    assert req.features == {}


def test_single_predict_request_accepts_feature_values():
    req = SinglePredictRequest(features={"tenure_days": 365.0, "cancel_count": 2.0})
    assert req.features["tenure_days"] == 365.0


# ── SinglePredictResponse ─────────────────────────────────


def test_single_predict_response_fields():
    resp = SinglePredictResponse(churn_probability=0.73, churn_prediction=1)
    assert resp.churn_probability == 0.73
    assert resp.churn_prediction == 1


# ── ExplainRequest ────────────────────────────────────────


def test_explain_request_default_top_n():
    req = ExplainRequest(features={"a": 1.0})
    assert req.top_n == 10


def test_explain_request_custom_top_n():
    req = ExplainRequest(features={"a": 1.0}, top_n=5)
    assert req.top_n == 5


# ── ExplainResponse ───────────────────────────────────────


def test_explain_response_structure():
    resp = ExplainResponse(
        probability=0.82,
        churn_prediction=1,
        top_features=[
            FeatureImpact(feature="tenure_days", impact=-0.41),
            FeatureImpact(feature="cancel_count", impact=0.28),
        ],
    )
    assert resp.probability == 0.82
    assert len(resp.top_features) == 2
    assert resp.top_features[0].feature == "tenure_days"


# ── ModelInfo ─────────────────────────────────────────────


def test_model_info_mlflow_run_id_is_optional():
    info = ModelInfo(
        model_name="customer-churn-lgb",
        version="1.0.0",
        trained_at="2026-06-21T18:00:00",
        val_logloss=0.13,
        val_auc=0.98,
        num_features=17,
        num_trees=10,
    )
    assert info.mlflow_run_id is None


def test_model_info_with_run_id():
    info = ModelInfo(
        model_name="customer-churn-lgb",
        version="1.0.0",
        trained_at="2026-06-21T18:00:00",
        val_logloss=0.13,
        val_auc=0.98,
        num_features=17,
        num_trees=10,
        mlflow_run_id="run-abc123",
    )
    assert info.mlflow_run_id == "run-abc123"
