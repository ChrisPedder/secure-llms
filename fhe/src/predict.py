import os
import pickle
import time

import numpy as np
import pandas as pd
from concrete.ml.sklearn import DecisionTreeClassifier


def load_model(model_dir: str) -> tuple[DecisionTreeClassifier, np.ndarray]:
    """Load training artifacts and reconstruct a fitted Concrete-ML model."""
    path = os.path.join(model_dir, "artifacts.pkl")
    with open(path, "rb") as f:
        artifacts = pickle.load(f)

    model = DecisionTreeClassifier(random_state=artifacts["random_state"])
    model.fit(artifacts["X_train"], artifacts["y_train"])
    return model, artifacts["X_train"]


def predict_new(
    model: DecisionTreeClassifier,
    compile_data: np.ndarray,
    input_path: str,
) -> np.ndarray:
    """Compile the FHE circuit, generate keys, and run encrypted inference on new samples."""
    df = pd.read_csv(input_path)
    if "Class" in df.columns:
        df = df.drop(columns=["Class"])
    X_new = df.values.astype(np.float32)

    print(f"Loaded {len(X_new)} samples from {input_path}")

    print("Compiling FHE circuit...")
    start = time.perf_counter()
    model.compile(compile_data)
    compile_time = time.perf_counter() - start
    print(f"  Compilation: {compile_time:.2f}s")

    print("Generating FHE keys...")
    start = time.perf_counter()
    model.fhe_circuit.client.keygen()
    keygen_time = time.perf_counter() - start
    print(f"  Key generation: {keygen_time:.2f}s")

    print(f"Running encrypted inference on {len(X_new)} samples...")
    start = time.perf_counter()
    predictions = model.predict(X_new, fhe="execute")
    inference_time = time.perf_counter() - start
    print(f"  Inference: {inference_time:.2f}s ({inference_time / len(X_new):.2f}s/sample)")

    return predictions
