from pathlib import Path
from typing import Optional

import lightgbm as lgb

from src.utils import load_config

_model: Optional[lgb.Booster] = None
_explainer = None  # shap.TreeExplainer — imported lazily to avoid slow startup


def get_model() -> lgb.Booster:
    if _model is None:
        raise RuntimeError("Model not loaded — run POST /pipeline/train first")
    return _model


def reload_model() -> None:
    global _model
    config = load_config()
    model_path = Path(config["paths"]["models"]) / "baseline_lgb.txt"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    _model = lgb.Booster(model_file=str(model_path))


def get_explainer():
    global _explainer, _model
    if _model is None:
        raise RuntimeError("Model not loaded — run POST /pipeline/train first")
    if _explainer is None:
        import shap
        _explainer = shap.TreeExplainer(_model)
    return _explainer


def reload_explainer() -> None:
    global _explainer
    _explainer = None  # re-created lazily on the next /predict/explain call
