"""POST /predict/single|batch|explain"""

import sqlite3

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# ── /predict/single ───────────────────────────────────────


def test_single_returns_probability_and_prediction(client: TestClient, sample_features: dict):
    r = client.post("/predict/single", json={"features": sample_features})
    assert r.status_code == 200

    data = r.json()
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["churn_prediction"] in (0, 1)


def test_single_prediction_consistent_with_threshold(client: TestClient, sample_features: dict):
    data = client.post("/predict/single", json={"features": sample_features}).json()
    expected = 1 if data["churn_probability"] >= 0.5 else 0
    assert data["churn_prediction"] == expected


def test_single_missing_features_filled_with_zero(client: TestClient):
    """Sending an empty feature dict should not crash — missing values become 0."""
    r = client.post("/predict/single", json={"features": {}})
    assert r.status_code == 200
    assert "churn_probability" in r.json()


def test_single_invalid_body_returns_422(client: TestClient):
    r = client.post("/predict/single", json={})  # missing 'features' key
    assert r.status_code == 422


def test_single_persists_to_db(client: TestClient, sample_features: dict):
    import src.api.database as db

    client.post("/predict/single", json={"features": sample_features})

    conn = sqlite3.connect(str(db.DB_PATH))
    rows = conn.execute("SELECT probability, prediction FROM predictions").fetchall()
    conn.close()

    assert len(rows) == 1
    prob, pred = rows[0]
    assert 0.0 <= prob <= 1.0
    assert pred in (0, 1)


def test_single_persists_features_as_json(client: TestClient, sample_features: dict):
    import json

    import src.api.database as db

    client.post("/predict/single", json={"features": sample_features})

    conn = sqlite3.connect(str(db.DB_PATH))
    row = conn.execute("SELECT features FROM predictions").fetchone()
    conn.close()

    saved = json.loads(row[0])
    assert saved == sample_features


# ── /predict/batch ────────────────────────────────────────


def test_batch_returns_predictions(client: TestClient, toy_model, monkeypatch):
    feature_cols = toy_model.feature_name()

    def mock_load(config):
        df = pd.DataFrame({col: np.random.random(5) for col in feature_cols})
        df["is_churn"] = 0
        return df

    import src.api.routers.predict as pred_router

    monkeypatch.setattr(pred_router, "load_processed_features", mock_load)

    r = client.post("/predict/batch")
    assert r.status_code == 200

    data = r.json()
    assert data["count"] == 5
    assert len(data["predictions"]) == 5


def test_batch_prediction_fields(client: TestClient, toy_model, monkeypatch):
    feature_cols = toy_model.feature_name()

    def mock_load(config):
        df = pd.DataFrame({col: [0.5] * 3 for col in feature_cols})
        df["is_churn"] = 0
        return df

    import src.api.routers.predict as pred_router

    monkeypatch.setattr(pred_router, "load_processed_features", mock_load)

    predictions = client.post("/predict/batch").json()["predictions"]
    for p in predictions:
        assert "churn_probability" in p
        assert "churn_prediction" in p
        assert 0.0 <= p["churn_probability"] <= 1.0


# ── /predict/explain ──────────────────────────────────────


def test_explain_returns_top_features(client: TestClient, sample_features: dict):
    r = client.post("/predict/explain", json={"features": sample_features, "top_n": 5})
    assert r.status_code == 200

    data = r.json()
    assert 0.0 <= data["probability"] <= 1.0
    assert data["churn_prediction"] in (0, 1)
    assert len(data["top_features"]) <= 5


def test_explain_feature_impact_schema(client: TestClient, sample_features: dict):
    data = client.post("/predict/explain", json={"features": sample_features, "top_n": 3}).json()

    for item in data["top_features"]:
        assert "feature" in item
        assert "impact" in item
        assert isinstance(item["impact"], float)


def test_explain_top_n_respected(client: TestClient, sample_features: dict):
    for top_n in (1, 3, 5):
        data = client.post(
            "/predict/explain", json={"features": sample_features, "top_n": top_n}
        ).json()
        assert len(data["top_features"]) <= top_n


def test_explain_features_sorted_by_absolute_impact(client: TestClient, sample_features: dict):
    data = client.post("/predict/explain", json={"features": sample_features, "top_n": 10}).json()

    impacts = [abs(f["impact"]) for f in data["top_features"]]
    assert impacts == sorted(impacts, reverse=True)
