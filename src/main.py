from utils import load_config
from pathlib import Path
import pandas as pd


def main():
    # Load config
    config = load_config()

    # Base project path (customer_churn/)
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Paths
    DATA_RAW = BASE_DIR / config["paths"]["data_raw"]

    # Load datasets
    train = pd.read_csv(DATA_RAW / config["files"]["train"])
    transactions = pd.read_csv(DATA_RAW / config["files"]["transactions"])
    user_logs = pd.read_csv(DATA_RAW / config["files"]["user_logs"])
    members = pd.read_csv(DATA_RAW / config["files"]["members"])
    sample_submission = pd.read_csv(DATA_RAW / config["files"]["sample_submission"])

    # Quick check
    print("Train shape:", train.shape)
    print("Transactions shape:", transactions.shape)
    print("User logs shape:", user_logs.shape)
    print("Members shape:", members.shape)
    print("Sample Submission shape:", sample_submission.shape)


if __name__ == "__main__":
    main()
