import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.database import init_db
from src.api.dependencies import reload_model
from src.api.routers import health, model, pipeline, predict


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Predictions database initialised")
    try:
        reload_model()
        logger.info("Model loaded successfully at startup")
    except FileNotFoundError:
        logger.warning("Model file not found — run POST /pipeline/train first")
    yield


app = FastAPI(
    title="Customer Churn API",
    description="ML inference service for customer churn prediction",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(model.router)
app.include_router(pipeline.router)
app.include_router(predict.router)
