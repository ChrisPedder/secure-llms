import argparse
import tempfile

from .compare import print_comparison, run_comparison
from .predict import load_model, predict_new
from .preprocess import load_and_preprocess
from .train import train_and_save


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
    sub = parser.add_subparsers(dest="command")

    train_p = sub.add_parser("train", help="Train models, compare on test set, save FHE model")
    train_p.add_argument(
        "--data-path",
        type=str,
        default="./data/creditcard.csv",
        help="Path to creditcard.csv (local path or s3://bucket/key)",
    )
    train_p.add_argument(
        "--model-dir",
        type=str,
        default="./model",
        help="Directory to save the trained model",
    )

    predict_p = sub.add_parser("predict", help="Run FHE inference on new samples")
    predict_p.add_argument(
        "--model-dir",
        type=str,
        default="./model",
        help="Directory containing the saved model",
    )
    predict_p.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to CSV file with new samples (same features as training data, no Class column)",
    )

    args = parser.parse_args()

    if args.command == "train":
        resolved_path = _resolve_data_path(args.data_path)
        print(f"Loading dataset from {resolved_path}...")
        X_train, X_test, y_train, y_test = load_and_preprocess(resolved_path)
        print(f"Dataset: {len(X_train)} train, {len(X_test)} test samples (balanced)\n")

        results = run_comparison(X_train, X_test, y_train, y_test)
        print_comparison(results)

        train_and_save(X_train, y_train, args.model_dir)
        print(f"\nModel saved to {args.model_dir}/")

    elif args.command == "predict":
        model, compile_data = load_model(args.model_dir)
        predictions = predict_new(model, compile_data, args.input)

        print(f"\n{'Sample':<10} {'Prediction':<15}")
        print("-" * 25)
        for i, pred in enumerate(predictions):
            label = "FRAUD" if pred == 1 else "legitimate"
            print(f"{i:<10} {label:<15}")
        print(f"\n{sum(predictions)}/{len(predictions)} flagged as fraud")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
