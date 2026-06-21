import threading
from datetime import datetime, timezone

import lightgbm as lgb
import pandas as pd
from fastapi import APIRouter, Depends

from src.api.database import save_prediction, save_predictions_bulk
from src.api.dependencies import get_explainer, get_model
from src.api.schemas import (
    BatchPredictResponse,
    ExplainRequest,
    ExplainResponse,
    FeatureImpact,
    SinglePredictRequest,
    SinglePredictResponse,
)
from src.utils import load_config, load_processed_features

router = APIRouter(prefix="/predict")


@router.post("/single", response_model=SinglePredictResponse)
def predict_single(
    request: SinglePredictRequest,
    model: lgb.Booster = Depends(get_model),
):
    expected = model.feature_name()
    df = pd.DataFrame([request.features]).reindex(columns=expected).fillna(0)
    prob = float(model.predict(df)[0])
    pred = int(prob >= 0.5)

    save_prediction(probability=prob, prediction=pred, features=request.features)

    return SinglePredictResponse(churn_probability=prob, churn_prediction=pred)


@router.post("/batch", response_model=BatchPredictResponse)
def predict_batch(model: lgb.Booster = Depends(get_model)):
    config = load_config()
    df = load_processed_features(config)

    X = df.drop(columns=["is_churn", "msno"], errors="ignore")
    num_cols = X.select_dtypes(include=["number"]).columns
    X[num_cols] = X[num_cols].fillna(0)
    drop_cols = X.select_dtypes(include=["object", "datetime64[ns]"]).columns
    X.drop(columns=drop_cols, inplace=True)

    probs = model.predict(X)

    ts = datetime.now(timezone.utc).isoformat()
    rows = [(ts, None, float(p), int(p >= 0.5)) for p in probs]
    threading.Thread(target=save_predictions_bulk, args=(rows,), daemon=True).start()

    predictions = [
        {"churn_probability": float(p), "churn_prediction": float(int(p >= 0.5))} for p in probs
    ]
    return BatchPredictResponse(count=len(predictions), predictions=predictions)


@router.post("/explain", response_model=ExplainResponse)
def predict_explain(
    request: ExplainRequest,
    model: lgb.Booster = Depends(get_model),
    explainer=Depends(get_explainer),
):
    expected = model.feature_name()
    df = pd.DataFrame([request.features]).reindex(columns=expected).fillna(0)

    prob = float(model.predict(df)[0])
    pred = int(prob >= 0.5)

    shap_result = explainer.shap_values(df)
    shap_vals = shap_result[1][0] if isinstance(shap_result, list) else shap_result[0]

    impacts = sorted(
        zip(expected, shap_vals),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    top_features = [
        FeatureImpact(feature=f, impact=round(float(v), 4)) for f, v in impacts[: request.top_n]
    ]

    return ExplainResponse(
        probability=prob,
        churn_prediction=pred,
        top_features=top_features,
    )
