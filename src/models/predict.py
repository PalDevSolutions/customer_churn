import logging
from pathlib import Path

import pandas as pd
import lightgbm as lgb

from src.utils import load_config, load_processed_features


# -------------------------
# Setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------------
# Load config & paths
# -------------------------
config = load_config()

MODEL_PATH = Path(config["paths"]["models"]) / "baseline_lgb.txt"
OUTPUT_PATH = Path(config["paths"]["models"]) / "predictions.csv"


# -------------------------
# Load model
# -------------------------
logger.info("Loading trained model...")
model = lgb.Booster(model_file=str(MODEL_PATH))


# -------------------------
# Load data
# -------------------------
df = load_processed_features(config)
logger.info(f"Loaded dataset: {df.shape}")


# -------------------------
# Prepare features
# -------------------------
X = df.drop(columns=["is_churn", "msno"], errors="ignore")

num_cols = X.select_dtypes(include=["number"]).columns
X[num_cols] = X[num_cols].fillna(0)

drop_cols = X.select_dtypes(include=["object", "datetime64[ns]"]).columns
X.drop(columns=drop_cols, inplace=True)

logger.info(f"Feature shape for inference: {X.shape}")


# -------------------------
# Predict
# -------------------------
logger.info("Running inference...")
df["churn_probability"] = model.predict(X)
df["churn_prediction"] = (df["churn_probability"] >= 0.5).astype(int)


# -------------------------
# Save results
# -------------------------
df[["churn_probability", "churn_prediction"]].to_csv(
    OUTPUT_PATH, index=False
)

logger.info(f"Predictions saved to {OUTPUT_PATH}")
logger.info("Inference completed.")