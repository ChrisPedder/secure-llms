from typing import Any

import numpy as np

from .baseline import run_baseline
from .encrypted import run_encrypted


def run_comparison(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, dict[str, Any]]:
    print("Running plaintext baseline...")
    plaintext = run_baseline(X_train, X_test, y_train, y_test)
    print(f"  Done ({plaintext['inference_time_s']:.4f}s inference)\n")

    print("Running FHE encrypted model...")
    encrypted = run_encrypted(X_train, X_test, y_train, y_test)
    print()

    return {"plaintext": plaintext, "encrypted": encrypted}


def print_comparison(results: dict[str, dict[str, Any]]) -> None:
    p = results["plaintext"]
    e = results["encrypted"]

    header = f"{'Metric':<22} {'Plaintext':>12} {'FHE':>12} {'Diff':>10}"
    sep = "-" * len(header)

    print(sep)
    print(header)
    print(sep)

    for metric in ["accuracy", "precision", "recall", "f1"]:
        pv = p[metric]
        ev = e[metric]
        diff = ev - pv
        print(f"{metric:<22} {pv:>12.4f} {ev:>12.4f} {diff:>+10.4f}")

    print(sep)

    print(f"{'train_time_s':<22} {p['train_time_s']:>12.4f} {e['train_time_s']:>12.4f}")
    print(f"{'compile_time_s':<22} {'N/A':>12} {e['compile_time_s']:>12.4f}")
    print(f"{'keygen_time_s':<22} {'N/A':>12} {e['keygen_time_s']:>12.4f}")
    print(f"{'inference_time_s':<22} {p['inference_time_s']:>12.4f} {e['inference_time_s']:>12.4f}")

    if p["inference_time_s"] > 0:
        slowdown = e["inference_time_s"] / p["inference_time_s"]
    else:
        slowdown = float("inf")
    print(sep)
    print(f"{'Inference slowdown':<22} {slowdown:>35.1f}x")
    print(sep)
