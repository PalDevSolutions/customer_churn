import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

DB_PATH = Path("data/predictions.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            features    TEXT,
            probability REAL    NOT NULL,
            prediction  INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_prediction(
    probability: float,
    prediction: int,
    features: Optional[dict] = None,
) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO predictions (timestamp, features, probability, prediction) VALUES (?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            json.dumps(features) if features else None,
            probability,
            prediction,
        ),
    )
    conn.commit()
    conn.close()


def save_predictions_bulk(rows: List[Tuple]) -> None:
    """rows: list of (timestamp, features_json_or_none, probability, prediction)"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.executemany(
        "INSERT INTO predictions (timestamp, features, probability, prediction) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
