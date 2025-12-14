from utils import load_config, load_datasets


def main():
    # Load configuration
    config = load_config()

    # Load datasets
    train, transactions, user_logs, members, sample_submission = load_datasets(config)

    # Quick sanity check
    print("Train shape:", train.shape)
    print("Transactions shape:", transactions.shape)
    print("User logs shape:", user_logs.shape)
    print("Members shape:", members.shape)
    print("Sample Submission shape:", sample_submission.shape)


if __name__ == "__main__":
    main()
