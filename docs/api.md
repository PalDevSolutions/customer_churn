# API Reference

Base URL: `http://localhost:8000` (local) or `http://<oracle-ip>:8000` (production)

Interactive docs: `GET /docs` (Swagger UI) · `GET /redoc` (ReDoc)

---

## GET /health

Liveness check. Used by Docker healthcheck and load balancers.

**Response `200`**
```json
{ "status": "ok" }
```

---

## Pipeline Endpoints

All pipeline endpoints are **asynchronous** — they start a background job and return a `job_id` immediately. Use `GET /pipeline/jobs/{job_id}` to poll for completion.

### Job Object

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending | running | done | failed",
  "result": { ... },
  "error": null
}
```

| Field | Type | Description |
|---|---|---|
| `job_id` | string (UUID) | Use to poll `/pipeline/jobs/{job_id}` |
| `status` | string | `pending` → `running` → `done` or `failed` |
| `result` | object or null | Populated when `status` is `done` |
| `error` | string or null | Populated when `status` is `failed` |

---

### POST /pipeline/preprocess

Runs the feature engineering pipeline. Loads the 4 raw CSVs, cleans and aggregates members, transactions, and user logs, and writes the output parquet file.

**Prerequisites:** Raw CSVs must exist in `data/raw/`

**Request body:** none

**Response `200`** — job object with `status: pending`

**Result when done:**
```json
{ }
```
*(result is empty — side effect is writing `data/processed/train_features.parquet`)*

**Example:**
```bash
curl -X POST http://localhost:8000/pipeline/preprocess
# {"job_id":"abc-123","status":"pending","result":null,"error":null}

curl http://localhost:8000/pipeline/jobs/abc-123
# {"job_id":"abc-123","status":"done","result":{},"error":null}
```

---

### POST /pipeline/train

Trains the LightGBM binary classifier on the processed features. Saves the model and feature importance plot, then hot-reloads the model into memory.

**Prerequisites:** `data/processed/train_features.parquet` must exist (run preprocess first)

**Request body:** none

**Response `200`** — job object with `status: pending`

**Result when done:**
```json
{
  "val_logloss": 0.1302,
  "val_auc": 0.9861,
  "num_features": 18,
  "num_trees": 347
}
```

**Side effects:**
- Writes `models/baseline_lgb.txt`
- Writes `models/feature_importance.png`
- Reloads model in memory — predictions are immediately available after this job finishes

**Example:**
```bash
curl -X POST http://localhost:8000/pipeline/train
curl http://localhost:8000/pipeline/jobs/<job_id>
```

---

### POST /pipeline/cv

Runs 5-fold stratified cross-validation to measure model stability. Does **not** save a model — evaluation only.

**Prerequisites:** `data/processed/train_features.parquet` must exist

**Request body:** none

**Response `200`** — job object with `status: pending`

**Result when done:**
```json
{
  "mean_logloss": 0.1294,
  "std_logloss": 0.0004,
  "mean_auc": 0.9854,
  "std_auc": 0.0002,
  "fold_loglosses": [0.1291, 0.1298, 0.1293, 0.1296, 0.1292],
  "fold_aucs": [0.9856, 0.9852, 0.9855, 0.9853, 0.9854]
}
```

---

### GET /pipeline/jobs/{job_id}

Polls the status of any pipeline job.

**Path parameter:** `job_id` — UUID returned by a pipeline POST endpoint

**Response `200`** — job object

**Response `404`**
```json
{ "detail": "Job not found" }
```

**Example:**
```bash
curl http://localhost:8000/pipeline/jobs/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

## Prediction Endpoints

These run **synchronously** — they return results directly in the response.

**Prerequisites:** A trained model must be loaded (either present at startup or trained via `/pipeline/train`).

---

### POST /predict/single

Predicts churn for a single user from a JSON feature dict. Missing features are filled with `0`.

**Request body:**
```json
{
  "features": {
    "bd": 28,
    "registered_via": 7,
    "tenure_days": 1200,
    "last_is_auto_renew": 1,
    "last_is_cancel": 0,
    "last_payment_plan_days": 30,
    "last_actual_amount_paid": 149,
    "last_has_discount": 0,
    "cancel_count": 0,
    "avg_auto_renew_rate": 1.0,
    "avg_paid": 149.0,
    "total_paid": 1788.0,
    "trans_count": 12,
    "trans_tenure_days": 365,
    "total_secs_sum": 3600000,
    "recent_total_secs": 450000,
    "recent_secs_ratio": 0.125
  }
}
```

**Response `200`:**
```json
{
  "churn_probability": 0.0821,
  "churn_prediction": 0
}
```

| Field | Type | Description |
|---|---|---|
| `churn_probability` | float | Model confidence the user will churn (0–1) |
| `churn_prediction` | int | `1` if `churn_probability >= 0.5`, else `0` |

**Example:**
```bash
curl -X POST http://localhost:8000/predict/single \
  -H "Content-Type: application/json" \
  -d '{"features": {"tenure_days": 1200, "last_is_auto_renew": 1}}'
```

---

### POST /predict/batch

Loads `data/processed/train_features.parquet` and runs the model over all rows. No request body needed.

**Request body:** none

**Response `200`:**
```json
{
  "count": 970960,
  "predictions": [
    { "churn_probability": 0.8377, "churn_prediction": 1.0 },
    { "churn_probability": 0.0412, "churn_prediction": 0.0 },
    { "churn_probability": 0.6103, "churn_prediction": 1.0 }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/predict/batch
```

---

## Typical Workflow

```
POST /pipeline/preprocess   →  poll jobs  →  done
POST /pipeline/train        →  poll jobs  →  done
POST /predict/batch         →  churn scores for all users
```

For ongoing monitoring:
```
POST /pipeline/cv           →  poll jobs  →  check mean AUC hasn't drifted
```

---

## Error Responses

| Status | When |
|---|---|
| `404` | `GET /pipeline/jobs/{id}` with unknown ID |
| `500` | Model not loaded and a predict endpoint is called |
| `422` | Request body fails validation (missing required fields, wrong types) |
