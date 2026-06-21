import json
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import logging

from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, roc_auc_score

import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils import load_config, load_processed_features


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_training() -> dict:
    config = load_config()

    MODEL_DIR = Path(config["paths"]["models"])
    MODEL_DIR.mkdir(exist_ok=True)

    df = load_processed_features(config)
    logger.info(f"Loaded dataset: {df.shape}")

    y = df["is_churn"]
    X = df.drop(columns=["is_churn", "msno"], errors="ignore")

    num_cols = X.select_dtypes(include=["number"]).columns
    X[num_cols] = X[num_cols].fillna(0)

    cat_cols = X.select_dtypes(include=["category"]).columns
    for col in cat_cols:
        X[col] = X[col].cat.add_categories("unknown").fillna("unknown")

    obj_cols = X.select_dtypes(include=["object"]).columns
    X[obj_cols] = X[obj_cols].fillna("unknown")

    drop_cols = X.select_dtypes(include=["object", "datetime64[ns]"]).columns
    X.drop(columns=drop_cols, inplace=True)

    constant_cols = [c for c in X.columns if X[c].nunique() <= 1]
    X.drop(columns=constant_cols, inplace=True)

    logger.info(f"Dropped {len(constant_cols)} constant columns")
    logger.info(f"Final feature shape: {X.shape}")

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "is_unbalance": True,
        "verbosity": -1,
        "seed": 42
    }

    mlflow.set_experiment("customer-churn")
    with mlflow.start_run(run_name="baseline-lgb"):
        mlflow.log_params(params)

        lgb_train = lgb.Dataset(X_train, label=y_train)
        lgb_valid = lgb.Dataset(X_valid, label=y_valid)

        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=1000,
            valid_sets=[lgb_train, lgb_valid],
            valid_names=["train", "valid"],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=100)
            ]
        )

        y_pred = model.predict(X_valid)
        val_logloss = log_loss(y_valid, y_pred)
        val_auc = roc_auc_score(y_valid, y_pred)

        logger.info(f"Validation Log Loss: {val_logloss:.4f}")
        logger.info(f"Validation AUC: {val_auc:.4f}")

        mlflow.log_metric("val_logloss", val_logloss)
        mlflow.log_metric("val_auc", val_auc)
        mlflow.log_metric("num_trees", model.num_trees())

        importance_path = MODEL_DIR / "feature_importance.png"
        lgb.plot_importance(model, max_num_features=20)
        plt.tight_layout()
        plt.savefig(importance_path)
        plt.close()
        mlflow.log_artifact(str(importance_path))

        model.save_model(MODEL_DIR / "baseline_lgb.txt")
        mlflow.lightgbm.log_model(model, "lgb-model")
        logger.info("Model saved to models/baseline_lgb.txt")

        run_id = mlflow.active_run().info.run_id

    meta = {
        "model_name": "customer-churn-lgb",
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "val_logloss": round(val_logloss, 4),
        "val_auc": round(val_auc, 4),
        "num_features": X.shape[1],
        "num_trees": model.num_trees(),
        "mlflow_run_id": run_id,
    }
    with open(MODEL_DIR / "model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    logger.info("Model metadata saved to models/model_meta.json")

    return {
        "val_logloss": round(val_logloss, 4),
        "val_auc": round(val_auc, 4),
        "num_features": X.shape[1],
        "num_trees": model.num_trees(),
        "mlflow_run_id": run_id,
    }


if __name__ == "__main__":
    print(run_training())
