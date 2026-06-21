# Required Changes — Priority Order

All changes needed to go from the current codebase to a working service with Docker deployment.
Apply them in the order listed — each priority block depends on the one above it.

---

## Priority 1 — Bug Fixes (blocks everything)

### 1.1 `src/data/preprocess.py` — wrong import name

**File:** `src/data/preprocess.py`
**Lines:** 4 and 24

**Current (broken):**
```python
from src.utils import load_config, load_datasets
...
train, transactions, user_logs, members, _ = load_datasets(config)
```

**Fix:**
```python
from src.utils import load_config, load_raw_datasets
...
train, transactions, user_logs, members, _ = load_raw_datasets(config)
```

**Why:** `load_datasets` does not exist in `src/utils.py`. The function is named `load_raw_datasets`. Running `python -m src.data.preprocess` currently crashes with `ImportError` before doing anything.

---

## Priority 2 — Refactor Scripts for API Compatibility

The pipeline scripts (`train_baseline.py`, `cv_baseline.py`) currently run all their logic at **module level** — meaning the code executes the moment Python imports the file. This makes them impossible to call from the API without triggering a full training run on import.

Both scripts need their logic wrapped in a function. The `if __name__ == "__main__"` block preserves the original CLI behaviour.

---

### 2.1 `src/models/train_baseline.py` — wrap in `run_training()`

**Current structure (broken for API):**
```python
# All of this runs on import:
config = load_config()
df = load_processed_features(config)
model = lgb.train(...)
plt.show()                         # also crashes in headless Docker
model.save_model(...)
```

**Required structure:**
```python
def run_training() -> dict:
    config = load_config()
    # ... all existing logic ...
    plt.savefig(...)   # replace plt.show() — no display in Docker
    plt.close()
    model.save_model(...)
    return {"val_logloss": ..., "val_auc": ..., "num_features": ..., "num_trees": ...}

if __name__ == "__main__":
    print(run_training())
```

**Two changes inside the function:**
- Replace `plt.show()` with `plt.close()` — `plt.show()` hangs in a headless container
- Add `matplotlib.use("Agg")` at the top of the file — forces non-interactive backend

**Why:** The API's `POST /pipeline/train` endpoint imports and calls `run_training()`. If code runs at import time, training starts the moment the server boots, not when the endpoint is called.

---

### 2.2 `src/models/cv_baseline.py` — wrap in `run_cv()`

**Current structure (broken for API):**
```python
# All of this runs on import:
config = load_config()
df = load_processed_features(config)
for fold, ... in skf.split(...):
    model = lgb.train(...)
logger.info("========== CV Results ==========")
```

**Required structure:**
```python
def run_cv() -> dict:
    config = load_config()
    # ... all existing logic ...
    return {
        "mean_logloss": ..., "std_logloss": ...,
        "mean_auc": ...,     "std_auc": ...,
        "fold_loglosses": [...], "fold_aucs": [...]
    }

if __name__ == "__main__":
    print(run_cv())
```

**Why:** Same reason as 2.1. The API's `POST /pipeline/cv` endpoint calls `run_cv()`. Module-level code runs on import.

---

## Priority 3 — Add API Dependencies

### 3.1 `requirements.txt` — add FastAPI and Uvicorn

**Add these two lines:**
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
```

**Why:** The service layer (`src/api/`) depends on these. Without them, `uvicorn src.api.app:app` fails with `ModuleNotFoundError`.

**Install after editing:**
```bash
pip install -r requirements.txt
```

---

## Priority 4 — Create the Service Layer

All new files — nothing to edit, just create. See [api.md](api.md) for what each endpoint does.

| File | What it does |
|------|-------------|
| `src/api/__init__.py` | Empty — marks directory as a package |
| `src/api/app.py` | FastAPI app, loads model at startup via `lifespan` |
| `src/api/schemas.py` | Pydantic request/response models (`JobResponse`, `PredictRequest`, etc.) |
| `src/api/dependencies.py` | Model singleton — `get_model()` and `reload_model()` |
| `src/api/routers/__init__.py` | Empty |
| `src/api/routers/health.py` | `GET /health` |
| `src/api/routers/pipeline.py` | `POST /pipeline/preprocess`, `/train`, `/cv`, `GET /pipeline/jobs/{id}` |
| `src/api/routers/predict.py` | `POST /predict/batch`, `POST /predict/single` |

**Test the server starts:**
```bash
uvicorn src.api.app:app --reload
# Open http://localhost:8000/docs
```

---

## Priority 5 — Docker

New files — create in the project root.

### 5.1 `Dockerfile`

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY config.json .
EXPOSE 8000
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key decisions:**
- `requirements.txt` is copied first and installed in its own layer — rebuilding after a code change reuses the cached pip layer
- `data/` and `models/` are **not** copied into the image; they are injected at runtime via volume mounts
- `python:3.9-slim` — small base image, no unnecessary system packages

### 5.2 `.dockerignore`

Excludes from build context (speeds up `docker build` and keeps the image clean):

```
venv/
__pycache__/
*.pyc
.git/
notebooks/
data/raw/
```

### 5.3 `docker-compose.yml`

```yaml
services:
  api:
    build: .
    image: customer-churn-api:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data       # processed features visible inside container
      - ./models:/app/models   # model artifacts persist across restarts
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3
```

**Test locally:**
```bash
docker compose up --build
```

---

## Priority 6 — Deploy to Oracle Cloud

### 6.1 One-time server setup (SSH in once)

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin curl
sudo usermod -aG docker $USER
# Log out and back in
```

### 6.2 Open port 8000 in OCI Console

OCI Console → Networking → VCN → Security Lists → Add Ingress Rule:
- Source CIDR: `0.0.0.0/0`
- Protocol: TCP
- Port: `8000`

Also run on the VM:
```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
```

### 6.3 `deploy.sh` — create and run

```bash
chmod +x deploy.sh
./deploy.sh ubuntu@<your-oracle-ip>
```

What the script does:
1. `docker build` locally
2. `docker save` → tar file
3. `scp` image + compose file + model artifacts to server
4. SSH → `docker load` + `docker compose up -d`
5. Hits `/health` and prints the live URL

**Full deployment guide:** [deployment.md](deployment.md)

---

## Summary Table

| # | Priority | File(s) | Type | Risk if skipped |
|---|----------|---------|------|----------------|
| 1 | Critical | `src/data/preprocess.py` | Bug fix | `ImportError` on preprocessing |
| 2 | Critical | `src/models/train_baseline.py` | Refactor | Training runs on API import; `plt.show()` hangs Docker |
| 3 | Critical | `src/models/cv_baseline.py` | Refactor | CV runs on API import |
| 4 | Required | `requirements.txt` | Dependency | API server won't start |
| 5 | Required | `src/api/` (8 files) | New | No API service |
| 6 | Required | `Dockerfile`, `.dockerignore`, `docker-compose.yml` | New | Can't containerise |
| 7 | Required | `deploy.sh` | New | Manual deployment only |
