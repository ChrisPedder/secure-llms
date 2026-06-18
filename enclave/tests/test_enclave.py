"""Tests for the enclave application logic (no vsock or real AWS calls)."""

import base64
import json
import os
from unittest.mock import MagicMock

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.enclave.app import decrypt_message, handle_request


def test_decrypt_message_direct_rsa():
    """Test direct RSA decryption path (short messages)."""
    plaintext = b"How should I invest?"
    mock_kms = MagicMock()
    mock_kms.decrypt.return_value = {"Plaintext": plaintext}

    payload = {
        "ciphertext": base64.b64encode(b"fake-ciphertext").decode(),
        "key_id": "arn:aws:kms:us-east-1:123456:key/test-key",
    }

    result = decrypt_message(mock_kms, payload)
    assert result == "How should I invest?"
    mock_kms.decrypt.assert_called_once()


def test_decrypt_message_hybrid():
    """Test hybrid decryption path (long messages wrapped with AES-GCM)."""
    data_key = os.urandom(32)
    nonce = os.urandom(12)
    plaintext = b"This is a longer message that exceeds the RSA plaintext limit"

    aesgcm = AESGCM(data_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    mock_kms = MagicMock()
    mock_kms.decrypt.return_value = {"Plaintext": data_key}

    payload = {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "encrypted_data_key": base64.b64encode(b"fake-wrapped-key").decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "key_id": "arn:aws:kms:us-east-1:123456:key/test-key",
    }

    result = decrypt_message(mock_kms, payload)
    assert result == plaintext.decode("utf-8")


def test_handle_request_unknown_action():
    """Test that unknown actions return an error."""
    result = handle_request(MagicMock(), MagicMock(), {"action": "unknown"})
    assert result["status"] == "error"
    assert "Unknown action" in result["error"]


def test_handle_request_decrypt_and_chat():
    """Test the full decrypt_and_chat flow with mocked KMS and Bedrock."""
    mock_kms = MagicMock()
    mock_kms.decrypt.return_value = {"Plaintext": b"What stocks should I buy?"}

    mock_bedrock = MagicMock()
    mock_bedrock.invoke_model.return_value = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "content": [{"text": "I recommend diversifying your portfolio."}]
                }).encode()
            )
        )
    }

    request = {
        "action": "decrypt_and_chat",
        "ciphertext": base64.b64encode(b"fake-ciphertext").decode(),
        "key_id": "arn:aws:kms:us-east-1:123456:key/test-key",
    }

    result = handle_request(mock_kms, mock_bedrock, request)
    assert result["status"] == "ok"
    assert "diversifying" in result["response"]

    call_args = mock_bedrock.invoke_model.call_args
    body = json.loads(call_args.kwargs["body"])
    assert body["system"] is not None
    assert body["messages"][0]["content"] == "What stocks should I buy?"
