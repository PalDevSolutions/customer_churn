# 📊 Customer Churn Prediction

This project implements an end-to-end machine learning pipeline to predict customer churn using user demographics, transaction history, and usage behavior.

The repository follows real-world ML engineering best practices, including feature engineering, baseline modeling, cross-validation, reproducibility, and production-ready artifacts.

---

## 📁 Project Structure

```
customer_churn/
│
├── data/
│   ├── raw/                    # Original datasets (CSV) – ignored by Git
│   │   ├── members_v3.csv
│   │   ├── transactions_v2.csv
│   │   ├── user_logs_v2.csv
│   │   ├── train_v2.csv
│   │   └── sample_submission_v2.csv
│   │
│   └── processed/              # Generated ML-ready features
│       └── train_features.parquet
│
├── models/
│   ├── baseline_lgb.txt        # Trained LightGBM model (native format)
│   └── feature_importance.png  # Feature importance visualization
│
├── notebooks/
│   ├── eda.ipynb               # Exploratory Data Analysis
│   └── test.ipynb              # Experiments & validation
│
├── src/
│   ├── utils.py                # Config & dataset loaders
│   ├── data/
│   │   └── preprocess.py       # Feature engineering pipeline
│   └── models/
│       ├── train_baseline.py   # Baseline model training
│       └── cv_baseline.py      # Cross-validation pipeline
│
├── config.json                 # Centralized configuration
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
```

---

## ⚙️ Environment Setup

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

**Git Bash / VS Code**

```bash
source venv/Scripts/activate
```

**CMD**

```bash
venv\Scripts\activate
```

**PowerShell**

```bash
.\venv\Scripts\Activate.ps1
```

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

**Key libraries:**

- numpy
- pandas
- scikit-learn
- lightgbm
- matplotlib
- jupyter
- pyarrow

---

## 🧩 Configuration

All paths and filenames are managed centrally using `config.json`.

```json
{
  "paths": {
    "data_raw": "data/raw/",
    "data_processed": "data/processed/",
    "models": "models/"
  },
  "files": {
    "train": "train_v2.csv",
    "transactions": "transactions_v2.csv",
    "user_logs": "user_logs_v2.csv",
    "members": "members_v3.csv",
    "sample_submission": "sample_submission_v2.csv",
    "train_features": "train_features.parquet"
  },
  "dates": {
    "transaction_date_format": "%Y%m%d",
    "reference_date": "2017-03-31"
  }
}
```

This design ensures portability, reproducibility, and zero hardcoded paths.

---

## 🧪 Feature Engineering

Feature engineering is implemented in:

```
src/data/preprocess.py
```

### Run Feature Engineering

```bash
python -m src.data.preprocess
```

**What This Step Does:**

- Loads raw datasets
- Cleans and validates demographic and transactional data
- Processes user activity logs using chunked reading
- Prevents data leakage using cutoff dates
- Produces ML-ready numeric features

**Output:**

```
data/processed/train_features.parquet
```

---

## 🤖 Baseline Model Training

Baseline model training is implemented using LightGBM.

**Training Script:**

```
src/models/train_baseline.py
```

### Run Training

```bash
python -m src.models.train_baseline
```

**Training Pipeline:**

1. Loads processed features
2. Handles missing values by data type
3. Removes unsupported and constant columns
4. Splits data into training and validation sets
5. Trains a LightGBM binary classifier
6. Applies early stopping
7. Evaluates performance
8. Saves model artifacts

### 📈 Baseline Results

Typical results:

- **Validation Log Loss:** ~0.130
- **Validation AUC:** ~0.986

This indicates strong probability calibration and excellent class separation.

---

## 🧪 Cross-Validation (Model Stability)

To ensure robustness and generalization, 5-Fold Stratified Cross-Validation is applied.

**Validation Script:**

```
src/models/cv_baseline.py
```

### Run Cross-Validation

```bash
python -m src.models.cv_baseline
```

### Cross-Validation Results

```
========== CV Results ==========
Mean Log Loss: 0.1294
Std  Log Loss: 0.0004

Mean AUC:      0.9854
Std  AUC:      0.0002
```

**Interpretation:**

- Extremely low standard deviation across folds
- Stable learning behavior
- No evidence of overfitting
- Model is suitable for production inference

---

## 📊 Feature Importance

Feature importance is automatically saved to:

```
models/feature_importance.png
```

Common top features include:

- Transaction tenure
- Membership tenure
- Auto-renew behavior
- Cancellation history
- Payment amount patterns

---

## 💾 Model Artifact

The trained model is stored in LightGBM native format:

```
models/baseline_lgb.txt
```

**Why This Format:**

- Version-stable
- Human-readable
- Secure (no pickle execution)
- Suitable for deployment

### 🔮 Inference Example

```python
import lightgbm as lgb

model = lgb.Booster(model_file="models/baseline_lgb.txt")
y_pred = model.predict(X_new)
```

`y_pred` represents churn probability per user.

---

## 📊 Exploratory Data Analysis

EDA notebooks are available in:

```
notebooks/
```

Launch Jupyter:

```bash
jupyter notebook
```

---

## 🚫 Git Ignore Rules

Ignored paths:

- `venv/`
- `data/raw/`
- `__pycache__/`

Large processed datasets and models are tracked using Git LFS.

---

## 🧠 Technologies Used

- Python 3.9+
- Pandas & NumPy
- Scikit-learn
- LightGBM
- Matplotlib
- Jupyter Notebook
- PyArrow

---

## 🚀 Next Steps

- Train final model on full dataset (`train_full.py`)
- Batch prediction pipeline (`predict.py`)
- Threshold optimization
- API or dashboard deployment

---

## ✅ Summary

This repository demonstrates a production-oriented ML workflow with:

- Config-driven pipelines
- Feature leakage prevention
- Robust cross-validation
- Reproducible artifacts
- Deployment-ready models
