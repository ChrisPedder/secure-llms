import argparse
import os
import time

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from .predict import load_model

FEATURE_NAMES = [f"V{i}" for i in range(1, 29)] + ["Time", "Amount"]

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

_state = {
    "model": None,
    "compile_data": None,
    "samples": None,
    "ready": False,
}


def _init_model(model_dir: str, data_path: str | None) -> None:
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

    if data_path and os.path.exists(data_path):
        df = pd.read_csv(data_path)
        fraud = df[df["Class"] == 1].head(10)
        legit = df[df["Class"] == 0].sample(n=10, random_state=42)
        _state["samples"] = pd.concat([fraud, legit]).reset_index(drop=True)
        print(f"  Loaded {len(_state['samples'])} example samples")

    _state["ready"] = True
    print("Model ready for predictions")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/status")
def status():
    return jsonify({"ready": _state["ready"]})


@app.route("/samples")
def samples():
    if _state["samples"] is None:
        return jsonify({"samples": []})
    df = _state["samples"]
    result = []
    for i, row in df.iterrows():
        result.append({
            "index": int(i),
            "label": "FRAUD" if row["Class"] == 1 else "legitimate",
            "actual": int(row["Class"]),
            "amount": round(float(row["Amount"]), 2),
            "features": {name: round(float(row[name]), 6) for name in FEATURE_NAMES},
        })
    return jsonify({"samples": result})


@app.route("/predict-steps", methods=["POST"])
def predict_steps():
    if not _state["ready"]:
        return jsonify({"error": "Model not loaded yet"}), 503

    model = _state["model"]
    circuit = model.fhe_circuit
    data = request.json
    features = data.get("features", {})

    values = [features.get(name, 0.0) for name in FEATURE_NAMES]
    X = np.array([values], dtype=np.float32)

    # Step 1: Quantize
    t0 = time.perf_counter()
    q_input = model.quantize_input(X)
    t_quantize = time.perf_counter() - t0

    # Step 2: Encrypt
    t0 = time.perf_counter()
    encrypted = circuit.encrypt(q_input)
    ct_bytes = encrypted.serialize()
    t_encrypt = time.perf_counter() - t0

    # Step 3: Compute on encrypted data
    t0 = time.perf_counter()
    encrypted_result = circuit.run(encrypted)
    ct_result_bytes = encrypted_result.serialize()
    t_compute = time.perf_counter() - t0

    # Step 4: Decrypt
    t0 = time.perf_counter()
    decrypted = circuit.decrypt(encrypted_result)
    t_decrypt = time.perf_counter() - t0

    # Step 5: Dequantize and classify
    dequantized = model.dequantize_output(decrypted.reshape(1, -1))
    prediction = int(np.argmax(dequantized, axis=1)[0])
    probabilities = dequantized[0].tolist()

    return jsonify({
        "steps": {
            "input": {
                "values": dict(zip(FEATURE_NAMES, [round(v, 6) for v in values], strict=True)),
            },
            "quantized": {
                "values": q_input[0].tolist(),
                "time_ms": round(t_quantize * 1000, 2),
            },
            "encrypted": {
                "size_bytes": len(ct_bytes),
                "hex_preview": ct_bytes[:48].hex(),
                "time_ms": round(t_encrypt * 1000, 2),
            },
            "computed": {
                "size_bytes": len(ct_result_bytes),
                "hex_preview": ct_result_bytes[:48].hex(),
                "time_ms": round(t_compute * 1000, 2),
            },
            "decrypted": {
                "raw": decrypted.flatten().tolist(),
                "time_ms": round(t_decrypt * 1000, 2),
            },
            "output": {
                "probabilities": probabilities,
                "prediction": prediction,
                "label": "FRAUD" if prediction == 1 else "legitimate",
            },
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="FHE Fraud Detection Web UI")
    parser.add_argument("--model-dir", default="./model", help="Path to saved model")
    parser.add_argument("--data-path", default="./data/creditcard.csv",
                        help="Path to dataset for example samples")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    _init_model(args.model_dir, args.data_path)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
