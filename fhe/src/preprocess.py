import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def validate_dataset(data_path: str) -> Path:
    path = Path(data_path)
    if not path.exists():
        print(
            f"Error: Dataset not found at '{path}'.\n\n"
            "To obtain the dataset:\n"
            "  1. Go to https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud\n"
            "  2. Download creditcard.csv\n"
            "  3. Place it at: fhe/data/creditcard.csv\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def load_and_preprocess(
    data_path: str,
    test_size: float = 0.3,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    path = validate_dataset(data_path)
    df = pd.read_csv(path)

    fraud = df[df["Class"] == 1]
    non_fraud = df[df["Class"] == 0].sample(n=len(fraud), random_state=random_state)
    balanced = pd.concat([fraud, non_fraud]).sample(frac=1, random_state=random_state)

    X = balanced.drop(columns=["Class"]).values
    y = balanced["Class"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y,
    )

    return X_train, X_test, y_train, y_test
