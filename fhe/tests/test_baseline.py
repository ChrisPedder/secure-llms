import numpy as np

from src.baseline import run_baseline


def test_run_baseline_returns_metrics():
    rng = np.random.RandomState(42)
    X_train = rng.randn(80, 10)
    y_train = (rng.rand(80) > 0.5).astype(int)
    X_test = rng.randn(20, 10)
    y_test = (rng.rand(20) > 0.5).astype(int)

    result = run_baseline(X_train, X_test, y_train, y_test)

    assert "accuracy" in result
    assert "precision" in result
    assert "recall" in result
    assert "f1" in result
    assert "train_time_s" in result
    assert "inference_time_s" in result
    assert 0.0 <= result["accuracy"] <= 1.0
