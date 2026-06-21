"""Unit tests for src/api/database.py — SQLite persistence layer."""

import json
import sqlite3


def _row_count(db_path) -> int:
    conn = sqlite3.connect(str(db_path))
    n = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    conn.close()
    return n


# ── init_db ───────────────────────────────────────────────


def test_init_db_creates_file(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.init_db()

    assert (tmp_path / "test.db").exists()


def test_init_db_creates_predictions_table(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    conn.close()

    assert "predictions" in tables


def test_init_db_is_idempotent(tmp_path, monkeypatch):
    """Calling init_db() twice must not raise or duplicate the table."""
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")

    db.init_db()
    db.init_db()  # should be a no-op


# ── save_prediction ───────────────────────────────────────


def test_save_prediction_inserts_row(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    db.save_prediction(probability=0.85, prediction=1, features={"x": 1.0})

    assert _row_count(tmp_path / "test.db") == 1


def test_save_prediction_values_stored_correctly(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    db.save_prediction(probability=0.72, prediction=1, features={"a": 0.5, "b": 1.0})

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    row = conn.execute("SELECT probability, prediction, features FROM predictions").fetchone()
    conn.close()

    prob, pred, feat_json = row
    assert prob == pytest.approx(0.72)
    assert pred == 1
    assert json.loads(feat_json) == {"a": 0.5, "b": 1.0}


def test_save_prediction_without_features(tmp_path, monkeypatch):
    """Batch predictions do not store individual feature dicts."""
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    db.save_prediction(probability=0.2, prediction=0)

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    feat_json = conn.execute("SELECT features FROM predictions").fetchone()[0]
    conn.close()

    assert feat_json is None


def test_save_prediction_timestamp_is_set(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    db.save_prediction(probability=0.5, prediction=0)

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    ts = conn.execute("SELECT timestamp FROM predictions").fetchone()[0]
    conn.close()

    assert ts is not None and len(ts) > 0


# ── save_predictions_bulk ────────────────────────────────


def test_save_predictions_bulk_inserts_all_rows(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    rows = [("2026-06-21T00:00:00", None, 0.1 * i, int(0.1 * i >= 0.5)) for i in range(10)]
    db.save_predictions_bulk(rows)

    assert _row_count(tmp_path / "test.db") == 10


def test_save_predictions_bulk_correct_values(tmp_path, monkeypatch):
    import src.api.database as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    db.save_predictions_bulk([("2026-01-01T00:00:00", None, 0.9, 1)])

    conn = sqlite3.connect(str(tmp_path / "test.db"))
    prob, pred = conn.execute("SELECT probability, prediction FROM predictions").fetchone()
    conn.close()

    assert prob == pytest.approx(0.9)
    assert pred == 1


import pytest  # noqa: E402  (needed for approx — placed here to keep imports grouped)
