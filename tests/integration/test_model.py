"""GET /model/info"""

from fastapi.testclient import TestClient


def test_model_info_404_before_training(client: TestClient):
    """Without model_meta.json the endpoint returns 404."""
    r = client.get("/model/info")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_model_info_returns_metadata(client_with_meta: TestClient):
    r = client_with_meta.get("/model/info")
    assert r.status_code == 200

    data = r.json()
    assert data["model_name"] == "customer-churn-lgb"
    assert data["version"] == "1.0.0"
    assert data["trained_at"] == "2026-06-21T18:00:00"
    assert data["val_auc"] == 0.9861
    assert data["val_logloss"] == 0.1302
    assert data["mlflow_run_id"] == "test-run-abc123"


def test_model_info_numeric_fields_are_floats(client_with_meta: TestClient):
    data = client_with_meta.get("/model/info").json()
    assert isinstance(data["val_logloss"], float)
    assert isinstance(data["val_auc"], float)
    assert isinstance(data["num_features"], int)
    assert isinstance(data["num_trees"], int)
