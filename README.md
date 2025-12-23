# 📊 Customer Churn Prediction

This project implements an end-to-end machine learning pipeline to predict customer churn using user demographics, transaction history, and usage behavior.

The repository follows real-world ML engineering best practices, including feature engineering, baseline modeling, cross-validation, reproducibility, and production-ready artifacts.

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
│   ├── feature_importance.png  # Feature importance visualization
│   └── predictions.csv         # Offline inference output
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
│       ├── cv_baseline.py      # Cross-validation pipeline
│       └── predict.py          # Offline batch inference
│
├── config.json                 # Centralized configuration
├── requirements.txt            # Python dependencies
├── README.md
└── .gitignore
```

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

```cmd
venv\Scripts\activate
```

**PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

Key libraries used:

- numpy
- pandas
- scikit-learn
- lightgbm
- matplotlib
- jupyter
- pyarrow

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

## 🧪 Feature Engineering

Feature engineering is implemented in: `src/data/preprocess.py`

### Run Feature Engineering

```bash
python -m src.data.preprocess
```

### What This Step Does

- Loads raw datasets
- Cleans demographic and transactional data
- Processes user activity logs using chunk-based reading
- Prevents data leakage using cutoff dates
- Generates ML-ready numeric features

### Output

```
data/processed/train_features.parquet
```

## 🤖 Baseline Model Training

Baseline model training is implemented using LightGBM.

**Training Script:** `src/models/train_baseline.py`

### Run Training

```bash
python -m src.models.train_baseline
```

### Training Pipeline

- Loads processed features
- Handles missing values by data type
- Removes unsupported and constant columns
- Splits data into training and validation sets
- Trains a LightGBM binary classifier
- Applies early stopping
- Evaluates performance
- Saves model artifacts

### Baseline Results

- **Validation Log Loss:** ~0.130
- **Validation AUC:** ~0.986

This indicates strong probability calibration and excellent churn separation.

## 🧪 Cross-Validation (Model Stability)

To ensure robustness and generalization, 5-fold stratified cross-validation is applied.

**Validation Script:** `src/models/cv_baseline.py`

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

### Interpretation

- Extremely stable performance across folds
- No evidence of overfitting
- Model is suitable for production inference

## 📊 Feature Importance

Feature importance is automatically saved to: `models/feature_importance.png`

Common top features include:

- Transaction tenure
- Membership tenure
- Auto-renew behavior
- Cancellation history
- Payment amount patterns

## 💾 Model Artifact

The trained model is stored in LightGBM native format: `models/baseline_lgb.txt`

### Why This Format

- Stable across LightGBM versions
- Human-readable
- Secure (no pickle execution)
- Deployment-friendly

## 🔮 Offline Inference (Batch Prediction)

The project includes an offline inference script that applies the trained model to processed features and generates churn predictions in batch mode.

This step simulates real-world production workflows where predictions are generated asynchronously or in bulk.

### 📄 Inference Script

`src/models/predict.py`

### ▶️ How to Run Inference

Ensure that:

- Feature engineering has been completed
- The baseline model has been trained

Then run:

```bash
python -m src.models.predict
```

### 📥 Input Data

The inference script automatically loads: `data/processed/train_features.parquet`

No raw data is used at inference time.

During execution, the script:

- Drops non-feature columns (is_churn, msno)
- Fills missing numeric values with 0
- Aligns features with the trained model

### 🤖 What the Script Does

- Loads the trained LightGBM model
- Loads processed feature data
- Aligns features with model expectations
- Generates churn probabilities
- Applies a default decision threshold (0.5)
- Saves results to disk

### 📤 Output

Predictions are saved to: `models/predictions.csv`

The output contains:

| Column            | Description                            |
| ----------------- | -------------------------------------- |
| churn_probability | Probability of churn                   |
| churn_prediction  | Binary label (1 = churn, 0 = no churn) |

Example output:

```csv
churn_probability,churn_prediction
0.8377,1
0.4161,0
0.8516,1
```

### 📊 Interpretation

- `churn_probability` reflects model confidence
- `churn_prediction` is computed using: `churn_probability >= 0.5`
- The threshold can be tuned based on business objectives

## 📊 Exploratory Data Analysis

EDA notebooks are available in: `notebooks/`

Launch Jupyter:

```bash
jupyter notebook
```

## 🚫 Git Ignore & LFS Rules

### Ignored paths:

- `venv/`
- `data/raw/`
- `__pycache__/`

### Large files tracked using Git LFS:

- `*.csv`
- `*.parquet`
- `*.png`
- `models/*.txt`

## 🧠 Technologies Used

- Python 3.9+
- Pandas & NumPy
- Scikit-learn
- LightGBM
- Matplotlib
- Jupyter Notebook
- PyArrow
