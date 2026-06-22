"""
Shared fixtures for all tests.

toy_model   — lightweight LightGBM trained on synthetic data (session scope)
sample_features — one row of feature values matching the toy model
client      — FastAPI TestClient with patched DB path, model injected, reload no-op
client_with_meta — same as client but also provides a model_meta.json
"""

import json

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Feature columns the toy model is trained on.
# These are a representative subset of the real preprocessing output.
FEATURE_COLS = [
    "bd",
    "registered_via",
    "tenure_days",
    "last_is_auto_renew",
    "last_is_cancel",
    "last_payment_plan_days",
    "last_actual_amount_paid",
    "last_has_discount",
    "cancel_count",
    "avg_auto_renew_rate",
    "avg_paid",
    "total_paid",
    "trans_count",
    "trans_tenure_days",
    "total_secs_sum",
    "recent_total_secs",
    "recent_secs_ratio",
]


@pytest.fixture(scope="session")
def toy_model() -> lgb.Booster:
    """
    Tiny LightGBM binary classifier trained on synthetic data.
    Session-scoped so it is built only once per test run.
    """
    np.random.seed(42)
    n = 300
    X = pd.DataFrame({col: np.random.random(n) for col in FEATURE_COLS})
    y = (np.random.random(n) > 0.8).astype(int)
    dataset = lgb.Dataset(X, label=y)
    params = {
        "objective": "binary",
        "num_leaves": 4,
        "verbosity": -1,
        "seed": 42,
    }
    return lgb.train(params, dataset, num_boost_round=10)


@pytest.fixture
def sample_features() -> dict:
    """One synthetic feature row compatible with toy_model."""
    return {col: 0.5 for col in FEATURE_COLS}


@pytest.fixture
def client(toy_model, tmp_path, monkeypatch) -> TestClient:
    """
    TestClient with:
    - SQLite DB redirected to a temp directory
    - model singleton set to toy_model (no disk read)
    - reload_model patched to no-op so lifespan does not overwrite the model
    - _explainer reset to None so each test starts without a cached explainer
    """
    import src.api.database as db
    import src.api.dependencies as deps

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(deps, "_model", toy_model)
    monkeypatch.setattr(deps, "_explainer", None)
    monkeypatch.setattr(deps, "reload_model", lambda: None)

    from src.api.app import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def client_with_meta(toy_model, tmp_path, monkeypatch) -> TestClient:
    """
    Same as client but also writes a model_meta.json to a temp path
    so GET /model/info returns data instead of 404.
    """
    import src.api.database as db
    import src.api.dependencies as deps
    import src.api.routers.model as model_router

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(deps, "_model", toy_model)
    monkeypatch.setattr(deps, "_explainer", None)
    monkeypatch.setattr(deps, "reload_model", lambda: None)

    meta_file = tmp_path / "model_meta.json"
    meta_file.write_text(
        json.dumps(
            {
                "model_name": "customer-churn-lgb",
                "version": "1.0.0",
                "trained_at": "2026-06-21T18:00:00",
                "val_logloss": 0.1302,
                "val_auc": 0.9861,
                "num_features": len(FEATURE_COLS),
                "num_trees": 10,
                "mlflow_run_id": "test-run-abc123",
            }
        )
    )
    monkeypatch.setattr(model_router, "_META_PATH", meta_file)

    from src.api.app import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
