from pathlib import Path

import numpy as np
import pandas as pd

from src.predict import load_model, predict_new
from src.train import train_and_save


def _make_data():
    rng = np.random.RandomState(42)
    X = rng.randn(100, 5).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.int64)
    return X, y


def test_train_and_save_creates_artifacts(tmp_path: Path):
    X, y = _make_data()
    model = train_and_save(X, y, str(tmp_path))
    assert (tmp_path / "artifacts.pkl").exists()
    assert model.predict(X[:3]) is not None


def test_load_model_roundtrip(tmp_path: Path):
    X, y = _make_data()
    train_and_save(X, y, str(tmp_path))
    model, compile_data = load_model(str(tmp_path))
    preds = model.predict(X[:5])
    assert len(preds) == 5
    assert set(preds).issubset({0, 1})


def test_predict_new_from_csv(tmp_path: Path):
    X, y = _make_data()
    train_and_save(X, y, str(tmp_path / "model"))

    csv_path = tmp_path / "new_samples.csv"
    df = pd.DataFrame(X[:3], columns=[f"f{i}" for i in range(5)])
    df.to_csv(csv_path, index=False)

    model, compile_data = load_model(str(tmp_path / "model"))
    preds = predict_new(model, compile_data, str(csv_path))
    assert len(preds) == 3
    assert all(p in (0, 1) for p in preds)
