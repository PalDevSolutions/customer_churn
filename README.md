# Customer Churn Prediction

End-to-end ML pipeline to predict customer churn using user demographics, transaction history, and usage behavior. Includes a FastAPI service layer for inference and pipeline management, containerized with Docker and deployable to Oracle Cloud.

---

## Project Structure

```
customer_churn/
│
├── data/
│   ├── raw/                        # Original datasets (CSV) – ignored by Git
│   │   ├── members_v3.csv
│   │   ├── transactions_v2.csv
│   │   ├── user_logs_v2.csv
│   │   ├── train_v2.csv
│   │   └── sample_submission_v2.csv
│   └── processed/
│       ├── train_features.parquet  # Generated ML-ready features
│       └── predictions.db          # SQLite prediction log
│
├── models/
│   ├── baseline_lgb.txt            # Trained LightGBM model (native format)
│   ├── model_meta.json             # Model metadata (version, AUC, trained_at)
│   ├── feature_importance.png
│   └── predictions.csv             # Offline batch inference output
│
├── notebooks/
│   ├── eda.ipynb
│   └── test.ipynb
│
├── src/
│   ├── utils.py                    # Config & dataset loaders
│   ├── data/
│   │   └── preprocess.py           # Feature engineering pipeline
│   ├── models/
│   │   ├── train_baseline.py       # Baseline model training (MLflow tracked)
│   │   ├── cv_baseline.py          # Cross-validation (MLflow tracked)
│   │   └── predict.py              # Offline batch inference
│   └── api/
│       ├── app.py                  # FastAPI application + lifespan
│       ├── schemas.py              # Pydantic request/response models
│       ├── dependencies.py         # Model + SHAP explainer singletons
│       ├── database.py             # SQLite prediction persistence
│       └── routers/
│           ├── health.py           # GET /health
│           ├── model.py            # GET /model/info
│           ├── pipeline.py         # POST /pipeline/preprocess|train|cv
│           └── predict.py          # POST /predict/single|batch|explain
│
├── docs/
│   ├── api.md                      # Full API reference
│   ├── deployment.md               # Docker & Oracle Cloud deployment guide
│   └── changes.md                  # Implementation priority log
│
├── Makefile                        # Task runner (cross-platform)
├── pyproject.toml                  # Project metadata, ruff, pytest config
├── config.json                     # Centralized path & filename configuration
├── requirements.txt                # Pinned Python dependencies
├── Dockerfile
├── docker-compose.yml
└── deploy.sh                       # One-command Oracle Cloud deployment
```

---

## Quick Start

```bash
# 1. Create virtual environment
make venv

# 2. Activate it
source venv/Scripts/activate        # Git Bash / VS Code
# or: .\venv\Scripts\Activate.ps1   # PowerShell

# 3. Install dependencies
make install

# 4. Run the full ML pipeline
make pipeline                       # preprocess + train

# 5. Start the API
make run
```

Open `http://localhost:8000/docs` for the Swagger UI.

---

## Make Targets

Run `make help` to list all targets with descriptions.

### Environment

| Command | Description |
|---|---|
| `make venv` | Create virtual environment |
| `make install` | Install all dependencies from `requirements.txt` |

### API Server

| Command | Description |
|---|---|
| `make run` | Start API with hot-reload (development) |
| `make run-prod` | Start API without hot-reload (production-like) |

### ML Pipeline

| Command | Description |
|---|---|
| `make preprocess` | Feature engineering → `data/processed/train_features.parquet` |
| `make train` | Train LightGBM model → `models/baseline_lgb.txt` |
| `make cv` | 5-fold cross-validation |
| `make predict` | Offline batch inference → `models/predictions.csv` |
| `make pipeline` | `preprocess` + `train` in one shot |

### MLflow

| Command | Description |
|---|---|
| `make mlflow-ui` | Open experiment tracking UI at `http://localhost:5000` |

### Docker

| Command | Description |
|---|---|
| `make docker-build` | Build Docker image |
| `make docker-up` | Build and start container |
| `make docker-down` | Stop and remove containers |

### Code Quality

| Command | Description |
|---|---|
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make clean` | Remove `__pycache__` and `.pyc` files |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/model/info` | Model metadata (version, AUC, trained_at) |
| `POST` | `/pipeline/preprocess` | Run feature engineering (async job) |
| `POST` | `/pipeline/train` | Train model + reload into memory (async job) |
| `POST` | `/pipeline/cv` | Run cross-validation (async job) |
| `GET` | `/pipeline/jobs/{id}` | Poll job status |
| `POST` | `/predict/single` | Predict churn for one user (JSON features) |
| `POST` | `/predict/batch` | Predict churn for all users in parquet file |
| `POST` | `/predict/explain` | SHAP feature attribution for one user |

See [docs/api.md](docs/api.md) for full request/response schemas and examples.

---

## Baseline Results

| Metric | Value |
|---|---|
| Validation Log Loss | 0.130 |
| Validation AUC | 0.986 |
| CV Mean Log Loss | 0.1294 ± 0.0004 |
| CV Mean AUC | 0.9854 ± 0.0002 |

---

## Docker

```bash
make docker-up     # build + start
make docker-down   # stop
```

Data and models are volume-mounted — they persist outside the image and survive rebuilds.

See [docs/deployment.md](docs/deployment.md) for Oracle Cloud deployment.

---

## MLflow Experiment Tracking

Both training and cross-validation are tracked automatically. After running `make train` or `make cv`:

```bash
make mlflow-ui
# Open http://localhost:5000
```

Each run logs: hyperparameters, `val_logloss`, `val_auc`, `num_trees`, the feature importance chart, and the model artifact.

---

## Prediction Persistence

Every prediction made through the API is saved to `data/predictions.db` (SQLite):

```
predictions
├── id           INTEGER  primary key
├── timestamp    TEXT     UTC ISO-8601
├── features     TEXT     JSON (single predict only)
├── probability  REAL
└── prediction   INTEGER  0 or 1
```

---

## SHAP Explanations

```bash
curl -X POST http://localhost:8000/predict/explain \
  -H "Content-Type: application/json" \
  -d '{
    "features": {"tenure_days": 1200, "last_is_auto_renew": 1},
    "top_n": 5
  }'
```

```json
{
  "probability": 0.082,
  "churn_prediction": 0,
  "top_features": [
    { "feature": "trans_tenure_days", "impact": -0.4312 },
    { "feature": "last_is_auto_renew", "impact": -0.2105 },
    { "feature": "cancel_count",       "impact":  0.0871 }
  ]
}
```

Positive impact pushes toward churn; negative pushes away.

---

## Configuration

All paths and filenames are managed centrally in [config.json](config.json). No hardcoded paths anywhere in the codebase.

---

## Development

Install dev dependencies (ruff, pytest, httpx):

```bash
pip install -e ".[dev]"
```

```bash
make lint      # ruff check src/
make format    # ruff format src/
make clean     # remove __pycache__ / .pyc
```

Linting rules (configured in [pyproject.toml](pyproject.toml)): pycodestyle (E/W), pyflakes (F), isort (I), pyupgrade (UP).

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data | Pandas, NumPy, PyArrow |
| Model | LightGBM, scikit-learn |
| Explainability | SHAP |
| Experiment Tracking | MLflow |
| API | FastAPI, Uvicorn, Pydantic |
| Persistence | SQLite (stdlib) |
| Container | Docker, Docker Compose |
| Code Quality | Ruff |
| Notebooks | Jupyter |
