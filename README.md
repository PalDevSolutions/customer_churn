# Customer Churn Prediction

This project focuses on analyzing customer behavior and building machine learning models to predict customer churn using Python and Jupyter Notebooks.

---

## 📁 Project Structure

```
customer_churn/
│
├── data/
│   └── raw/
│       ├── members_v3.csv
│       ├── transactions_v2.csv
│       ├── user_logs_v2.csv
│       ├── train_v2.csv
│       └── sample_submission_v2.csv
│
├── notebooks/
│   └── test.ipynb
│
├── README.md
├── .gitignore
└── requirements.txt
```

---

## ⚙️ Environment Setup (Virtual Environment)

### 1️⃣ Create a Virtual Environment

Make sure Python is installed:

```bash
python --version
```

Create the virtual environment inside the project directory:

```bash
python -m venv venv
```

### 2️⃣ Activate the Virtual Environment

**Windows (Git Bash / VS Code):**

```bash
source venv/Scripts/activate
```

**Windows (CMD):**

```bash
venv\Scripts\activate
```

**Windows (PowerShell):**

```bash
.\venv\Scripts\Activate.ps1
```

Once activated, you should see:

```
(venv)
```

---

## 📦 Install Dependencies

Install all required libraries using:

```bash
pip install -r requirements.txt
```

Or install libraries manually:

```bash
pip install numpy pandas matplotlib scikit-learn jupyter
```

---

## 🧾 Export Installed Libraries

To export all installed libraries into a `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

⚠️ Make sure the virtual environment is activated before running this command.

---

## 🛑 Deactivate the Virtual Environment

When finished:

```bash
deactivate
```

---

## 🚫 Git Ignore

The virtual environment should not be committed to Git. Make sure `.gitignore` includes:

```
venv/
```

---

## 🚀 Running the Project

1. Activate the virtual environment
2. Start Jupyter Notebook:

```bash
jupyter notebook
```

3. Open `notebooks/test.ipynb`
4. Run the cells to explore the data and train models

---

## 🧠 Technologies Used

- Python
- Pandas & NumPy
- Scikit-learn
- Matplotlib
- Jupyter Notebook

---

## 📌 Notes

- Always activate the virtual environment before running the project
- Keep `requirements.txt` updated after installing new packages
- This setup ensures reproducibility across different machines
