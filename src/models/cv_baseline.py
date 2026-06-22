import numpy as np
import logging

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss, roc_auc_score

import lightgbm as lgb

from src.utils import load_config, load_processed_features


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_cv() -> dict:
    config = load_config()

    df = load_processed_features(config)
    logger.info(f"Loaded dataset: {df.shape}")

    y = df["is_churn"]
    X = df.drop(columns=["is_churn", "msno"], errors="ignore")

    num_cols = X.select_dtypes(include=["number"]).columns
    X[num_cols] = X[num_cols].fillna(0)

    drop_cols = X.select_dtypes(include=["object", "datetime64[ns]"]).columns
    X.drop(columns=drop_cols, inplace=True)

    logger.info(f"Final feature shape after cleaning: {X.shape}")

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

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    log_losses = []
    auc_scores = []

    for fold, (train_idx, valid_idx) in enumerate(skf.split(X, y), 1):
        logger.info(f"Starting fold {fold}")

        X_train, X_valid = X.iloc[train_idx], X.iloc[valid_idx]
        y_train, y_valid = y.iloc[train_idx], y.iloc[valid_idx]

        lgb_train = lgb.Dataset(X_train, label=y_train)
        lgb_valid = lgb.Dataset(X_valid, label=y_valid)

        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=1000,
            valid_sets=[lgb_valid],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=0)
            ]
        )

        y_pred = model.predict(X_valid)
        fold_logloss = log_loss(y_valid, y_pred)
        fold_auc = roc_auc_score(y_valid, y_pred)

        log_losses.append(fold_logloss)
        auc_scores.append(fold_auc)

        logger.info(f"Fold {fold} - Log Loss: {fold_logloss:.4f}, AUC: {fold_auc:.4f}")

    mean_logloss = float(np.mean(log_losses))
    std_logloss = float(np.std(log_losses))
    mean_auc = float(np.mean(auc_scores))
    std_auc = float(np.std(auc_scores))

    logger.info("========== CV Results ==========")
    logger.info(f"Mean Log Loss: {mean_logloss:.4f}")
    logger.info(f"Std Log Loss:  {std_logloss:.4f}")
    logger.info(f"Mean AUC:      {mean_auc:.4f}")
    logger.info(f"Std AUC:       {std_auc:.4f}")

    return {
        "mean_logloss": round(mean_logloss, 4),
        "std_logloss": round(std_logloss, 4),
        "mean_auc": round(mean_auc, 4),
        "std_auc": round(std_auc, 4),
        "fold_loglosses": [round(v, 4) for v in log_losses],
        "fold_aucs": [round(v, 4) for v in auc_scores],
    }


if __name__ == "__main__":
    print(run_cv())
