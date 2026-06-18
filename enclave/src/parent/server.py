"""Flask parent server: serves web UI, proxies encrypted chat requests to the enclave via vsock."""

import json
import os
import socket
import struct
import time
from pathlib import Path

import boto3
from flask import Flask, jsonify, request, send_from_directory

ENCLAVE_CID = int(os.environ.get("ENCLAVE_CID", "16"))
ENCLAVE_PORT = int(os.environ.get("ENCLAVE_PORT", "5000"))
KMS_KEY_ID = os.environ.get("KMS_KEY_ID", "")
PUBLISH_METRICS = os.environ.get("PUBLISH_METRICS", "false").lower() == "true"

STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))


def _send_to_enclave(payload: dict) -> dict:
    """Send a JSON request to the enclave over vsock and return the response."""
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    try:
        sock.settimeout(120)
        sock.connect((ENCLAVE_CID, ENCLAVE_PORT))

        data = json.dumps(payload).encode("utf-8")
        sock.sendall(struct.pack("!I", len(data)))
        sock.sendall(data)

        length_bytes = _recv_all(sock, 4)
        msg_length = struct.unpack("!I", length_bytes)[0]
        response_bytes = _recv_all(sock, msg_length)
        return json.loads(response_bytes.decode("utf-8"))
    finally:
        sock.close()


def _recv_all(sock: socket.socket, length: int) -> bytes:
    """Receive exactly `length` bytes from a socket."""
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before all data received")
        data += chunk
    return data


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/public-key")
def public_key():
    try:
        kms = boto3.client("kms")
        response = kms.get_public_key(KeyId=KMS_KEY_ID)
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            PublicFormat,
            load_der_public_key,
        )

        pub_key = load_der_public_key(response["PublicKey"])
        pem = pub_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        return jsonify({"public_key_pem": pem.decode("utf-8")})
    except Exception as e:
        return jsonify({"error": f"Failed to fetch public key: {e}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json()
    if not body or "ciphertext" not in body:
        return jsonify({"error": "Missing ciphertext"}), 400

    payload = {
        "action": "decrypt_and_chat",
        "ciphertext": body["ciphertext"],
        "key_id": KMS_KEY_ID,
    }

    if "encrypted_data_key" in body:
        payload["encrypted_data_key"] = body["encrypted_data_key"]
        payload["nonce"] = body["nonce"]

    try:
        result = _send_to_enclave(payload)
    except (ConnectionRefusedError, OSError):
        return jsonify({"error": "Enclave unavailable"}), 503

    if result.get("status") == "error":
        return jsonify({"error": result.get("error", "Unknown enclave error")}), 500

    _publish_request_metric()
    return jsonify({"response": result["response"]})


def _publish_request_metric():
    """Publish a CloudWatch metric to signal activity (for auto-teardown alarm)."""
    if not PUBLISH_METRICS:
        return
    try:
        cw = boto3.client("cloudwatch")
        cw.put_metric_data(
            Namespace="SecureLlms/Enclave",
            MetricData=[{
                "MetricName": "LastRequestTimestamp",
                "Value": time.time(),
                "Unit": "Seconds",
            }],
        )
    except Exception:
        pass


def main():
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
