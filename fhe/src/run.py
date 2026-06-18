import argparse
import tempfile

from .compare import print_comparison, run_comparison
from .preprocess import load_and_preprocess


def _resolve_data_path(data_path: str) -> str:
    if not data_path.startswith("s3://"):
        return data_path
    import boto3

    parts = data_path.replace("s3://", "").split("/", 1)
    bucket, key = parts[0], parts[1]
    local_path = tempfile.mktemp(suffix=".csv")
    print(f"Downloading s3://{bucket}/{key}...")
    boto3.client("s3").download_file(bucket, key, local_path)
    print(f"Downloaded to {local_path}")
    return local_path


def main() -> None:
    parser = argparse.ArgumentParser(description="FHE Fraud Detection with Concrete-ML")
    parser.add_argument("--local", action="store_true", help="Run in local mode")
    parser.add_argument(
        "--data-path",
        type=str,
        default="./data/creditcard.csv",
        help="Path to creditcard.csv (local path or s3://bucket/key)",
    )
    args = parser.parse_args()

    resolved_path = _resolve_data_path(args.data_path)
    print(f"Loading dataset from {resolved_path}...")
    X_train, X_test, y_train, y_test = load_and_preprocess(resolved_path)
    print(f"Dataset: {len(X_train)} train, {len(X_test)} test samples (balanced)\n")

    results = run_comparison(X_train, X_test, y_train, y_test)
    print_comparison(results)


if __name__ == "__main__":
    main()
