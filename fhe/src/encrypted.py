import time
from typing import Any

import numpy as np
from concrete.ml.sklearn import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def run_encrypted(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, Any]:
    model = DecisionTreeClassifier(random_state=42)

    print("  Training Concrete-ML model...")
    start = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - start
    print(f"  Training complete ({train_time:.2f}s)")

    print("  Compiling FHE circuit...")
    start = time.perf_counter()
    circuit = model.compile(X_train)
    compile_time = time.perf_counter() - start
    print(f"  Compilation complete ({compile_time:.2f}s)")

    print("  Generating FHE keys...")
    start = time.perf_counter()
    circuit.client.keygen()
    keygen_time = time.perf_counter() - start
    print(f"  Key generation complete ({keygen_time:.2f}s)")

    print(f"  Running encrypted inference on {len(X_test)} samples...")
    start = time.perf_counter()
    y_pred = model.predict(X_test, fhe="execute")
    inference_time = time.perf_counter() - start
    print(f"  Encrypted inference complete ({inference_time:.2f}s)")

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "train_time_s": train_time,
        "compile_time_s": compile_time,
        "keygen_time_s": keygen_time,
        "inference_time_s": inference_time,
    }
