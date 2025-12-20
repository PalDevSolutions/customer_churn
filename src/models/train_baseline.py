import numpy as np
from pathlib import Path
import logging

from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, roc_auc_score

import lightgbm as lgb
import matplotlib.pyplot as plt

from src.utils import load_config, load_processed_features


# -------------------------
# Setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

config = load_config()

MODEL_DIR = Path(config["paths"]["models"])
MODEL_DIR.mkdir(exist_ok=True)


# -------------------------
# Load data
# -------------------------
df = load_processed_features(config)
logger.info(f"Loaded dataset: {df.shape}")


# -------------------------
# Prepare features
# -------------------------
y = df["is_churn"]
X = df.drop(columns=["is_churn", "msno"], errors="ignore")

# Fill NaNs
num_cols = X.select_dtypes(include=["number"]).columns
X[num_cols] = X[num_cols].fillna(0)

cat_cols = X.select_dtypes(include=["category"]).columns
for col in cat_cols:
    X[col] = X[col].cat.add_categories("unknown").fillna("unknown")

obj_cols = X.select_dtypes(include=["object"]).columns
X[obj_cols] = X[obj_cols].fillna("unknown")

# Drop non-numeric columns not supported by LightGBM
drop_cols = X.select_dtypes(include=["object", "datetime64[ns]"]).columns
X.drop(columns=drop_cols, inplace=True)

# Drop constant columns
constant_cols = [c for c in X.columns if X[c].nunique() <= 1]
X.drop(columns=constant_cols, inplace=True)

logger.info(f"Dropped {len(constant_cols)} constant columns")
logger.info(f"Final feature shape: {X.shape}")


# -------------------------
# Train / Validation split
# -------------------------
X_train, X_valid, y_train, y_valid = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# -------------------------
# LightGBM Baseline
# -------------------------
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

# -------------------------
# Evaluation
# -------------------------
y_pred = model.predict(X_valid)

logger.info(f"Validation Log Loss: {log_loss(y_valid, y_pred):.4f}")
logger.info(f"Validation AUC: {roc_auc_score(y_valid, y_pred):.4f}")

# -------------------------
# Feature Importance
# -------------------------
lgb.plot_importance(model, max_num_features=20)
plt.tight_layout()
plt.savefig(MODEL_DIR / "feature_importance.png")
plt.show()

# -------------------------
# Save Model
# -------------------------
model.save_model(MODEL_DIR / "baseline_lgb.txt")
logger.info("Model saved to models/baseline_lgb.txt")
