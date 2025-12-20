# 📊 Customer Churn Prediction

This project implements an end-to-end machine learning pipeline to predict customer churn using user demographics, transaction history, and usage behavior.
The pipeline covers data preprocessing, feature engineering, baseline model training, and reusable inference artifacts, following clean, modular, and reproducible ML engineering practices.

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
│       └── train_baseline.py   # Baseline model training script
│
├── config.json                 # Centralized configuration
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
```

## ⚙️ Environment Setup

### 1️⃣ Create a Virtual Environment

```bash
python -m venv venv
```

### 2️⃣ Activate the Virtual Environment

**Windows (Git Bash / VS Code)**

```bash
source venv/Scripts/activate
```

**Windows (CMD)**

```cmd
venv\Scripts\activate
```

**Windows (PowerShell)**

```powershell
.\venv\Scripts\Activate.ps1
```

You should see:

```
(venv)
```

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

**Main libraries used:**

- numpy
- pandas
- scikit-learn
- lightgbm
- matplotlib
- jupyter
- pyarrow

## 🧩 Configuration (config.json)

All paths, filenames, and feature locations are managed centrally via `config.json`.

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

**This design ensures:**

- No hardcoded paths
- Easy portability
- Clean separation between raw and processed data

## 🧪 Feature Engineering Pipeline

The feature engineering logic is implemented in:

```
src/data/preprocess.py
```

### ▶️ Run Feature Engineering

```bash
python -m src.data.preprocess
```

### ✅ What this step does

- Loads raw datasets using `utils.load_raw_datasets`
- Cleans and processes:
  - Member demographics
  - Transaction history
  - User activity logs (chunk-based processing)
- Prevents data leakage using cutoff dates
- Generates ML-ready numeric features

### 📦 Output

Saved to:

```
data/processed/train_features.parquet
```

**Example logs:**

```
INFO - Loaded 970960 rows for train
INFO - Saved features to data/processed/train_features.parquet
INFO - Final shape: (970960, 28)
```

## 🤖 Training the Baseline Model

A baseline churn prediction model is trained using LightGBM on engineered behavioral features.

### 📄 Training Script

```
src/models/train_baseline.py
```

### ▶️ Run Model Training

From the project root:

```bash
python -m src.models.train_baseline
```

### ✅ What this script does

- Loads processed features via `load_processed_features`
- Handles missing values by data type
- Removes unsupported and constant columns
- Splits data into train / validation sets
- Trains a LightGBM binary classifier
- Applies early stopping
- Evaluates performance
- Saves trained artifacts

## 📈 Baseline Model Results

**Typical output:**

```
Validation Log Loss: 0.1301
Validation AUC: 0.9857
```

**Interpretation:**

- Log Loss ≈ 0.13 → Strong probability calibration
- AUC ≈ 0.99 → Excellent churn vs non-churn separation

This represents a high-quality baseline model prior to hyperparameter tuning or time-based validation.

## 📊 Feature Importance

After training, feature importance is automatically generated and saved to:

```
models/feature_importance.png
```

**Top predictive features include:**

- Transaction tenure
- Membership tenure
- Last payment amount
- Auto-renew behavior
- Cancellation history

## 💾 Saved Model Format

The trained model is saved in LightGBM's native format:

```
models/baseline_lgb.txt
```

**Why this format?**

- Stable across LightGBM versions
- Human-readable
- Secure (no pickle execution)
- Suitable for production deployment

## 🔮 Using the Model (Inference)

Example: loading the trained model and generating predictions.

```python
import lightgbm as lgb
import pandas as pd

model = lgb.Booster(model_file="models/baseline_lgb.txt")

# X_new must contain the same feature columns as training data
y_pred = model.predict(X_new)
```

`y_pred` represents the probability of churn for each user.

## 📊 Exploratory Data Analysis (EDA)

EDA notebooks are available in:

```
notebooks/
```

**Launch Jupyter:**

```bash
jupyter notebook
```

- `eda.ipynb` → Data exploration & insights
- `test.ipynb` → Experiments & validation checks

## 🚫 Git Ignore Rules

The following paths should not be committed:

- `venv/`
- `data/raw/`
- `__pycache__/`

Processed features and trained models may be committed for reproducibility.

## 🧠 Technologies Used

- Python 3.9+
- Pandas & NumPy
- Scikit-learn
- LightGBM
- Matplotlib
- Jupyter Notebook
- PyArrow (Parquet)

## 🚀 Next Steps

- Time-based validation (production realism)
- Feature enrichment
- Hyperparameter tuning
- Batch inference & deployment

## ✅ Final Note

This repository follows real-world ML engineering practices, including:

- Config-driven pipelines
- Clear separation of raw vs processed data
- Reproducible training
- Production-ready model artifacts
