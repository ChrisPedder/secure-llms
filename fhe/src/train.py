import os
import pickle

import numpy as np
from concrete.ml.sklearn import DecisionTreeClassifier


def train_and_save(
    X_train: np.ndarray,
    y_train: np.ndarray,
    model_dir: str,
) -> DecisionTreeClassifier:
    """Train a Concrete-ML model and save training artifacts for later FHE inference."""
    os.makedirs(model_dir, exist_ok=True)

    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    artifacts = {
        "X_train": X_train,
        "y_train": y_train,
        "random_state": 42,
    }
    with open(os.path.join(model_dir, "artifacts.pkl"), "wb") as f:
        pickle.dump(artifacts, f)

    return model
