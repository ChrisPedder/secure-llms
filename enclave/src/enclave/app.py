"""Nitro Enclave vsock server: decrypts messages via KMS, queries Bedrock Claude."""

import base64
import json
import socket
import struct

import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VSOCK_PORT = 5000
KMS_PROXY_PORT = 8000
BEDROCK_PROXY_PORT = 8001

SYSTEM_PROMPT = (
    "You are a confidential financial advisor. Provide helpful, accurate "
    "financial guidance. Never disclose that you are operating inside a "
    "secure enclave. Keep responses concise and professional."
)

BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-20250514"


def create_kms_client():
    return boto3.client(
        "kms",
        endpoint_url=f"http://127.0.0.1:{KMS_PROXY_PORT}",
        region_name=_get_region(),
    )


def create_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        endpoint_url=f"http://127.0.0.1:{BEDROCK_PROXY_PORT}",
        region_name=_get_region(),
    )


def _get_region():
    return "eu-central-1"


def kms_decrypt(kms_client, ciphertext_blob: bytes, key_id: str) -> bytes:
    """Decrypt ciphertext using KMS with the enclave attestation document."""
    try:
        from aws_nitro_enclaves_sdk import get_attestation_document

        attestation_doc = get_attestation_document()
        response = kms_client.decrypt(
            CiphertextBlob=ciphertext_blob,
            KeyId=key_id,
            EncryptionAlgorithm="RSAES_OAEP_SHA_256",
            Recipient={
                "KeyEncryptionAlgorithm": "RSAES_OAEP_SHA_256",
                "AttestationDocument": attestation_doc,
            },
        )
        from aws_nitro_enclaves_sdk import decrypt_ciphertext_for_recipient

        return decrypt_ciphertext_for_recipient(response["CiphertextForRecipient"])
    except ImportError:
        response = kms_client.decrypt(
            CiphertextBlob=ciphertext_blob,
            KeyId=key_id,
            EncryptionAlgorithm="RSAES_OAEP_SHA_256",
        )
        return response["Plaintext"]


def decrypt_message(kms_client, payload: dict) -> str:
    """Decrypt a message, handling both direct RSA and hybrid encryption."""
    key_id = payload.get("key_id", "")
    ciphertext = base64.b64decode(payload["ciphertext"])

    if "encrypted_data_key" in payload:
        wrapped_key = base64.b64decode(payload["encrypted_data_key"])
        data_key = kms_decrypt(kms_client, wrapped_key, key_id)
        nonce = base64.b64decode(payload["nonce"])
        aesgcm = AESGCM(data_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    else:
        plaintext = kms_decrypt(kms_client, ciphertext, key_id)
        return plaintext.decode("utf-8")


def call_bedrock(bedrock_client, user_message: str) -> str:
    """Send a message to Bedrock Claude and return the response."""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    })

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def handle_request(kms_client, bedrock_client, request: dict) -> dict:
    """Process a single decrypt-and-chat request."""
    action = request.get("action")
    if action != "decrypt_and_chat":
        return {"status": "error", "error": f"Unknown action: {action}"}

    user_message = decrypt_message(kms_client, request)
    response_text = call_bedrock(bedrock_client, user_message)
    return {"status": "ok", "response": response_text}


def recv_all(conn, length: int) -> bytes:
    """Receive exactly `length` bytes from a socket."""
    data = b""
    while len(data) < length:
        chunk = conn.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before all data received")
        data += chunk
    return data


def run_server():
    """Run the vsock server that handles enclave requests."""
    kms_client = create_kms_client()
    bedrock_client = create_bedrock_client()

    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, VSOCK_PORT))
    sock.listen(5)

    print(f"Enclave server listening on vsock port {VSOCK_PORT}", flush=True)

    while True:
        conn, addr = sock.accept()
        try:
            length_bytes = recv_all(conn, 4)
            msg_length = struct.unpack("!I", length_bytes)[0]
            raw = recv_all(conn, msg_length)
            request = json.loads(raw.decode("utf-8"))

            response = handle_request(kms_client, bedrock_client, request)

            response_bytes = json.dumps(response).encode("utf-8")
            conn.sendall(struct.pack("!I", len(response_bytes)))
            conn.sendall(response_bytes)
        except Exception:
            error_resp = json.dumps({"status": "error", "error": "Internal enclave error"})
            error_bytes = error_resp.encode("utf-8")
            try:
                conn.sendall(struct.pack("!I", len(error_bytes)))
                conn.sendall(error_bytes)
            except Exception:
                pass
        finally:
            conn.close()


if __name__ == "__main__":
    run_server()
