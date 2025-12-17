import pandas as pd
import numpy as np
from pathlib import Path
from utils import load_config, load_datasets
import logging

# -------------------------
# Setup
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CUTOFF_DATE = pd.Timestamp("2017-03-31")
LOGS_START_DATE = pd.Timestamp("2016-12-01")
RECENT_START_DATE = pd.Timestamp("2017-03-01")

def load_initial_data():
    config = load_config()

    train, transactions, user_logs, members, _ = load_datasets(config)

    # IMPORTANT: ignore user_logs here (we'll process it in chunks later)
    del user_logs

    # Ensure sorting as required by task
    transactions = transactions.sort_values(
        ["msno", "transaction_date"]
    )

    logger.info(f"Loaded {len(train)} rows for train")
    logger.info(f"Loaded {len(members)} rows for members")
    logger.info(f"Loaded {len(transactions)} rows for transactions")

    return config, train, members, transactions

# -------------------------
# process members_v3.csv
# -------------------------
def process_members(members):
    members = members.copy()

    # Age cleaning
    members["bd"] = np.clip(members["bd"], 0, 100)
    members.loc[members["bd"] == 0, "bd"] = np.nan

    # Gender
    members["gender"] = members["gender"].fillna("unknown")

    # Tenure
    members["tenure_days"] = (
        CUTOFF_DATE - members["registration_init_time"]
    ).dt.days

    # Age groups
    members["age_group"] = pd.cut(
        members["bd"],
        bins=[0, 18, 35, 50, 100],
        labels=["0-18", "19-35", "36-50", "51+"]
    )

    return members.set_index("msno")

# -------------------------
# process transactions_v2.csv
# -------------------------
def process_transactions(trans):
    trans = trans.copy()

    # Leakage prevention
    trans = trans[
        trans["transaction_date"] <= trans["membership_expire_date"]
    ]

    # Remove duplicates
    trans = trans.drop_duplicates(
        subset=["msno", "transaction_date"],
        keep="last"
    )

    # Discounts
    trans["discount_amount"] = (
        trans["plan_list_price"] - trans["actual_amount_paid"]
    )
    trans["has_discount"] = (trans["discount_amount"] > 0).astype(int)

    # Last transaction
    last_trans = (
        trans.groupby("msno")
        .tail(1)
        .set_index("msno")
    )[
        [
            "is_auto_renew",
            "is_cancel",
            "payment_plan_days",
            "actual_amount_paid",
            "has_discount",
        ]
    ].add_prefix("last_")

    # Aggregations
    trans_agg = trans.groupby("msno").agg(
        cancel_count=("is_cancel", "sum"),
        avg_auto_renew_rate=("is_auto_renew", "mean"),
        avg_paid=("actual_amount_paid", "mean"),
        total_paid=("actual_amount_paid", "sum"),
        trans_count=("transaction_date", "count"),
        first_trans_date=("transaction_date", "min"),
    )

    # Tenure
    trans_agg["trans_tenure_days"] = (
        CUTOFF_DATE - trans_agg["first_trans_date"]
    ).dt.days

    trans_agg = trans_agg.drop(columns="first_trans_date")

    return pd.concat([last_trans, trans_agg], axis=1)

def process_user_logs(config, sample_msnos):
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_raw = base_dir / config["paths"]["data_raw"]
    logs_path = data_raw / "user_logs_v2.csv"

    overall_agg = []
    recent_agg = []

    for chunk in pd.read_csv(
        logs_path,
        chunksize=1_000_000,
        parse_dates=["date"]
    ):
        chunk = chunk[chunk["msno"].isin(sample_msnos)]
        chunk = chunk[chunk["date"] >= LOGS_START_DATE]

        chunk["total_secs"] = np.clip(chunk["total_secs"], 0, 86400)

        overall = chunk.groupby("msno").agg(
            num_25_sum=("num_25", "sum"),
            num_50_sum=("num_50", "sum"),
            num_75_sum=("num_75", "sum"),
            num_985_sum=("num_985", "sum"),
            num_100_sum=("num_100", "sum"),
            num_unq_sum=("num_unq", "sum"),
            total_secs_sum=("total_secs", "sum"),
        )

        recent = chunk[chunk["date"] >= RECENT_START_DATE].groupby("msno").agg(
            recent_total_secs=("total_secs", "sum")
        )

        overall_agg.append(overall)
        recent_agg.append(recent)

    overall_df = pd.concat(overall_agg).groupby("msno").sum()
    recent_df = pd.concat(recent_agg).groupby("msno").sum()

    logs_features = overall_df.join(recent_df, how="left").fillna(0)
    logs_features["recent_secs_ratio"] = (
        logs_features["recent_total_secs"] /
        logs_features["total_secs_sum"].replace(0, np.nan)
    ).fillna(0)

    return logs_features

def build_features():
    config, train, members, trans = load_initial_data()

    members_f = process_members(members)
    trans_f = process_transactions(trans)

    sample_msnos = train["msno"].sample(frac=0.1, random_state=42)
    logs_f = process_user_logs(config, sample_msnos)

    final_df = (
        train.set_index("msno")
        .join(members_f, how="left")
        .join(trans_f, how="left")
        .join(logs_f, how="left")
    )

    final_df = final_df.fillna(0)

    assert len(final_df) == len(train)

    output_path = Path("data/processed/train_features.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(output_path)

    logger.info(f"Saved features to {output_path}")
    logger.info(f"Final shape: {final_df.shape}")

if __name__ == "__main__":
    build_features()
