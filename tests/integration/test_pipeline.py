"""POST /pipeline/preprocess|train|cv  and  GET /pipeline/jobs/{id}"""

import time

from fastapi.testclient import TestClient


def _wait_for_job(client: TestClient, job_id: str, timeout: float = 3.0) -> dict:
    """Poll until the job is done or failed (or timeout)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = client.get(f"/pipeline/jobs/{job_id}")
        data = r.json()
        if data["status"] in ("done", "failed"):
            return data
        time.sleep(0.05)
    return client.get(f"/pipeline/jobs/{job_id}").json()


# ── Job lifecycle ──────────────────────────────────────────


def test_get_job_not_found(client: TestClient):
    r = client.get("/pipeline/jobs/does-not-exist")
    assert r.status_code == 404


def test_job_response_schema(client: TestClient, monkeypatch):
    import src.data.preprocess as pp

    monkeypatch.setattr(pp, "build_features", lambda: None)

    r = client.post("/pipeline/preprocess")
    assert r.status_code == 200

    data = r.json()
    assert "job_id" in data
    assert data["status"] in ("pending", "running", "done")
    assert "result" in data
    assert "error" in data


# ── Preprocess ────────────────────────────────────────────


def test_preprocess_job_completes(client: TestClient, monkeypatch):
    import src.data.preprocess as pp

    monkeypatch.setattr(pp, "build_features", lambda: None)

    r = client.post("/pipeline/preprocess")
    job_id = r.json()["job_id"]

    result = _wait_for_job(client, job_id)
    assert result["status"] == "done"


def test_preprocess_job_captures_error(client: TestClient, monkeypatch):
    import src.data.preprocess as pp

    monkeypatch.setattr(
        pp, "build_features", lambda: (_ for _ in ()).throw(RuntimeError("disk full"))
    )

    r = client.post("/pipeline/preprocess")
    job_id = r.json()["job_id"]

    result = _wait_for_job(client, job_id)
    assert result["status"] == "failed"
    assert "disk full" in result["error"]


# ── Train ─────────────────────────────────────────────────


def test_train_job_completes(client: TestClient, monkeypatch):
    import src.api.dependencies as deps
    import src.models.train_baseline as tb

    fake_result = {
        "val_logloss": 0.13,
        "val_auc": 0.98,
        "num_features": 17,
        "num_trees": 10,
        "mlflow_run_id": "fake-run",
    }
    monkeypatch.setattr(tb, "run_training", lambda: fake_result)
    monkeypatch.setattr(deps, "reload_model", lambda: None)
    monkeypatch.setattr(deps, "reload_explainer", lambda: None)

    r = client.post("/pipeline/train")
    job_id = r.json()["job_id"]

    result = _wait_for_job(client, job_id)
    assert result["status"] == "done"
    assert result["result"]["val_auc"] == 0.98


# ── CV ────────────────────────────────────────────────────


def test_cv_job_completes(client: TestClient, monkeypatch):
    import src.models.cv_baseline as cv

    fake_result = {
        "mean_logloss": 0.13,
        "std_logloss": 0.001,
        "mean_auc": 0.98,
        "std_auc": 0.001,
        "fold_loglosses": [0.13] * 5,
        "fold_aucs": [0.98] * 5,
        "mlflow_run_id": "fake-cv-run",
    }
    monkeypatch.setattr(cv, "run_cv", lambda: fake_result)

    r = client.post("/pipeline/cv")
    job_id = r.json()["job_id"]

    result = _wait_for_job(client, job_id)
    assert result["status"] == "done"
    assert result["result"]["mean_auc"] == 0.98
