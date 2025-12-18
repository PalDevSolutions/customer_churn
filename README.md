# 📊 Customer Churn Prediction

This project builds an end-to-end machine learning pipeline to predict customer churn based on user demographics, transaction history, and usage behavior. It includes data preprocessing, feature engineering, and model-ready datasets, with a clean and reproducible project structure.

## 📁 Project Structure

```
customer_churn/
│
├── data/
│   ├── raw/                    # Original datasets (CSV)
│   │   ├── members_v3.csv
│   │   ├── transactions_v2.csv
│   │   ├── user_logs_v2.csv
│   │   ├── train_v2.csv
│   │   └── sample_submission_v2.csv
│   │
│   └── processed/              # Generated features
│       └── train_features.parquet
│
├── notebooks/
│   ├── eda.ipynb              # Exploratory Data Analysis
│   └── test.ipynb             # Experiments & testing
│
├── src/
│   ├── utils.py               # Config & dataset loaders
│   └── data/
│       └── preprocess.py      # Feature engineering pipeline
│
├── config.json                # Centralized paths & filenames
├── requirements.txt           # Python dependencies
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

Install all required packages:

```bash
pip install -r requirements.txt
```

**Main libraries used:**

- numpy
- pandas
- scikit-learn
- matplotlib
- jupyter
- pyarrow (for parquet support)

## 🧩 Configuration (config.json)

All dataset paths and filenames are managed centrally via `config.json`.

**Example:**

```json
{
  "paths": {
    "data_raw": "data/raw"
  },
  "files": {
    "train": "train_v2.csv",
    "transactions": "transactions_v2.csv",
    "user_logs": "user_logs_v2.csv",
    "members": "members_v3.csv",
    "sample_submission": "sample_submission_v2.csv"
  }
}
```

This makes the pipeline portable and easy to maintain.

## 🧪 Running the Feature Engineering Pipeline

The main preprocessing logic lives in:

```
src/data/preprocess.py
```

### ▶️ Run Feature Engineering

From the project root:

```bash
python -m src.data.preprocess
```

### ✅ What this does:

- Loads datasets using `utils.py`
- Cleans and processes:
  - Member demographics
  - Transaction history
  - User activity logs (chunk-based processing)
- Generates ML-ready features
- Saves the final dataset to:
  ```
  data/processed/train_features.parquet
  ```

You should see logs like:

```
INFO: Loaded 970960 rows for train
INFO: Saved features to data/processed/train_features.parquet
INFO: Final shape: (970960, 28)
```

## 📊 Exploratory Data Analysis (EDA)

EDA notebooks are located in:

```
notebooks/
```

### ▶️ Launch Jupyter

```bash
jupyter notebook
```

**Open:**

- `eda.ipynb` → data exploration & insights
- `test.ipynb` → experiments and validation

## 🧠 Utilities Explained

### `src/utils.py`

- Loads configuration (`load_config`)
- Loads raw datasets (`load_datasets`)
- Keeps file access logic centralized

### `src/data/preprocess.py`

- End-to-end feature engineering
- Date parsing, aggregation, leakage prevention
- Produces final ML-ready dataset

## 🚫 Git Ignore Rules

The following should not be committed:

- `venv/`
- `data/raw/`
- `__pycache__/`

Processed features may be committed for reproducibility.

## 🧠 Technologies Used

- Python 3.9+
- Pandas & NumPy
- Scikit-learn
- Matplotlib
- Jupyter Notebook
- PyArrow (Parquet support)
