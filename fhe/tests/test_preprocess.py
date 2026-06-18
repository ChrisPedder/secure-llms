from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.preprocess import load_and_preprocess, validate_dataset


def _make_fake_csv(path: Path, n_fraud: int = 50, n_legit: int = 500) -> None:
    rng = np.random.RandomState(42)
    rows = []
    for _ in range(n_legit):
        row = list(rng.randn(28)) + [rng.uniform(0, 100000), rng.uniform(0, 300), 0]
        rows.append(row)
    for _ in range(n_fraud):
        row = list(rng.randn(28)) + [rng.uniform(0, 100000), rng.uniform(0, 300), 1]
        rows.append(row)
    cols = [f"V{i}" for i in range(1, 29)] + ["Time", "Amount", "Class"]
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(path, index=False)


def test_validate_dataset_missing(tmp_path: Path):
    with pytest.raises(SystemExit):
        validate_dataset(str(tmp_path / "nonexistent.csv"))


def test_validate_dataset_exists(tmp_path: Path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("dummy")
    result = validate_dataset(str(csv_path))
    assert result == csv_path


def test_load_and_preprocess_shapes(tmp_path: Path):
    csv_path = tmp_path / "creditcard.csv"
    _make_fake_csv(csv_path, n_fraud=50, n_legit=500)

    X_train, X_test, y_train, y_test = load_and_preprocess(str(csv_path))

    assert X_train.shape[1] == 30
    assert X_test.shape[1] == 30
    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    assert len(X_train) + len(X_test) == 100


def test_load_and_preprocess_balanced(tmp_path: Path):
    csv_path = tmp_path / "creditcard.csv"
    _make_fake_csv(csv_path, n_fraud=50, n_legit=500)

    X_train, X_test, y_train, y_test = load_and_preprocess(str(csv_path))

    all_y = np.concatenate([y_train, y_test])
    n_fraud = (all_y == 1).sum()
    n_legit = (all_y == 0).sum()
    assert n_fraud == n_legit
