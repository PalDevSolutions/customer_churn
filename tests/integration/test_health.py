"""GET /health"""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_works_without_model(tmp_path, monkeypatch):
    """Health endpoint must succeed even when no model is loaded."""
    import src.api.database as db
    import src.api.dependencies as deps

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(deps, "_model", None)
    monkeypatch.setattr(deps, "reload_model", lambda: None)

    from src.api.app import app

    with TestClient(app) as c:
        r = c.get("/health")

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
