# ─────────────────────────────────────────────
#  Customer Churn — project task runner
# ─────────────────────────────────────────────

# Detect OS so the same Makefile works on Windows (Git Bash) and Linux/macOS
ifeq ($(OS),Windows_NT)
    PYTHON   := venv/Scripts/python
    PIP      := venv/Scripts/pip
    UVICORN  := venv/Scripts/uvicorn
    MLFLOW   := venv/Scripts/mlflow
else
    PYTHON   := venv/bin/python
    PIP      := venv/bin/pip
    UVICORN  := venv/bin/uvicorn
    MLFLOW   := venv/bin/mlflow
endif

.PHONY: help install venv run run-prod \
        preprocess train cv predict pipeline \
        mlflow-ui \
        docker-build docker-up docker-down \
        lint format clean

# ── Default target ────────────────────────────
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Environment ───────────────────────────────
venv: ## Create virtual environment
	python -m venv venv

install: ## Install all dependencies from requirements.txt
	$(PIP) install -r requirements.txt

# ── API server ────────────────────────────────
run: ## Start API server with hot-reload (development)
	$(UVICORN) src.api.app:app --reload

run-prod: ## Start API server without hot-reload (production-like)
	$(UVICORN) src.api.app:app --host 0.0.0.0 --port 8000

# ── ML pipeline ───────────────────────────────
preprocess: ## Run feature engineering → data/processed/train_features.parquet
	$(PYTHON) -m src.data.preprocess

train: ## Train LightGBM model → models/baseline_lgb.txt
	$(PYTHON) -m src.models.train_baseline

cv: ## Run 5-fold cross-validation
	$(PYTHON) -m src.models.cv_baseline

predict: ## Run offline batch inference → models/predictions.csv
	$(PYTHON) -m src.models.predict

pipeline: preprocess train ## Run full pipeline: preprocess then train

# ── MLflow ────────────────────────────────────
mlflow-ui: ## Open MLflow experiment tracking UI at http://localhost:5000
	$(MLFLOW) ui

# ── Docker ────────────────────────────────────
docker-build: ## Build Docker image
	docker build -t customer-churn-api:latest .

docker-up: ## Build and start container with docker compose
	docker compose up --build

docker-down: ## Stop and remove containers
	docker compose down

# ── Code quality ──────────────────────────────
lint: ## Lint source code with ruff
	$(PYTHON) -m ruff check src/

format: ## Format source code with ruff
	$(PYTHON) -m ruff format src/

# ── Housekeeping ──────────────────────────────
clean: ## Remove __pycache__ and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
