import json
from pathlib import Path


def load_config(config_path="config.json"):
    """
    Load configuration file and return it as a dictionary.

    Args:
        config_path (str): Path to config.json file

    Returns:
        dict: Parsed configuration
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config
