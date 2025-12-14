import json
from pathlib import Path
import pandas as pd


def load_config(config_path="config.json"):
    """
    Load configuration file and return it as a dictionary.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def load_datasets(config):
    """
    Load all datasets using paths defined in config.

    Args:
        config (dict): Loaded configuration

    Returns:
        tuple: train, transactions, user_logs, members, sample_submission
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_raw = base_dir / config["paths"]["data_raw"]

    train = pd.read_csv(data_raw / config["files"]["train"])
    transactions = pd.read_csv(data_raw / config["files"]["transactions"])
    user_logs = pd.read_csv(data_raw / config["files"]["user_logs"])
    members = pd.read_csv(data_raw / config["files"]["members"])
    sample_submission = pd.read_csv(
        data_raw / config["files"]["sample_submission"]
    )

    return train, transactions, user_logs, members, sample_submission
