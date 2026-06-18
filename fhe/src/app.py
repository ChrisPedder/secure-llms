import argparse
import os
import time

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from .predict import load_model

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

_state = {
    "model": None,
    "compile_data": None,
    "ready": False,
    "fhe_mode": "simulate",
}


def _init_model(model_dir: str) -> None:
    print(f"Loading model from {model_dir}...")
    model, compile_data = load_model(model_dir)

    print("Compiling FHE circuit...")
    start = time.perf_counter()
    model.compile(compile_data)
    print(f"  Compiled in {time.perf_counter() - start:.2f}s")

    print("Generating FHE keys...")
    start = time.perf_counter()
    model.fhe_circuit.client.keygen()
    print(f"  Keys generated in {time.perf_counter() - start:.2f}s")

    _state["model"] = model
    _state["compile_data"] = compile_data
    _state["ready"] = True
    print("Model ready for predictions")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/status")
def status():
    return jsonify({
        "ready": _state["ready"],
        "fhe_mode": _state["fhe_mode"],
    })


@app.route("/mode", methods=["POST"])
def set_mode():
    mode = request.json.get("mode", "simulate")
    if mode not in ("simulate", "execute"):
        return jsonify({"error": "Mode must be 'simulate' or 'execute'"}), 400
    _state["fhe_mode"] = mode
    return jsonify({"fhe_mode": mode})


@app.route("/predict", methods=["POST"])
def predict():
    if not _state["ready"]:
        return jsonify({"error": "Model not loaded yet"}), 503

    model = _state["model"]
    fhe_mode = _state["fhe_mode"]

    if "file" in request.files:
        file = request.files["file"]
        df = pd.read_csv(file)
    elif request.is_json:
        df = pd.DataFrame(request.json["samples"])
    else:
        return jsonify({"error": "Send a CSV file or JSON with 'samples' array"}), 400

    if "Class" in df.columns:
        labels = df["Class"].values.tolist()
        df = df.drop(columns=["Class"])
    else:
        labels = None

    X = df.values.astype(np.float32)

    start = time.perf_counter()
    preds = model.predict(X, fhe=fhe_mode)
    elapsed = time.perf_counter() - start

    results = []
    for i, pred in enumerate(preds):
        row = {
            "index": i,
            "prediction": int(pred),
            "label": "FRAUD" if pred == 1 else "legitimate",
        }
        if labels is not None:
            row["actual"] = int(labels[i])
            row["correct"] = int(pred) == int(labels[i])
        results.append(row)

    fraud_count = sum(1 for r in results if r["prediction"] == 1)
    accuracy = None
    if labels is not None:
        accuracy = sum(1 for r in results if r.get("correct")) / len(results)

    return jsonify({
        "results": results,
        "summary": {
            "total": len(results),
            "fraud": fraud_count,
            "legitimate": len(results) - fraud_count,
            "accuracy": accuracy,
            "inference_time_s": round(elapsed, 3),
            "per_sample_s": round(elapsed / len(results), 3) if results else 0,
            "fhe_mode": fhe_mode,
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="FHE Fraud Detection Web UI")
    parser.add_argument("--model-dir", default="./model", help="Path to saved model")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    _init_model(args.model_dir)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
