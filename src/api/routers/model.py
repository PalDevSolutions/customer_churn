import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.schemas import ModelInfo

router = APIRouter(prefix="/model")

_META_PATH = Path("models/model_meta.json")


@router.get("/info", response_model=ModelInfo)
def model_info():
    if not _META_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No model metadata found — run POST /pipeline/train first",
        )
    with open(_META_PATH) as f:
        return ModelInfo(**json.load(f))
