"""Tests for the Flask parent server routes (vsock mocked)."""

from unittest.mock import patch

import pytest

from src.parent.server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Confidential Financial Advisor" in resp.data


def test_static_css(client):
    resp = client.get("/style.css")
    assert resp.status_code == 200
    assert b"font-family" in resp.data


def test_static_js(client):
    resp = client.get("/app.js")
    assert resp.status_code == 200
    assert b"encryptMessage" in resp.data


def test_chat_missing_ciphertext(client):
    resp = client.post("/chat", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Missing ciphertext" in data["error"]


def test_chat_no_body(client):
    resp = client.post("/chat", content_type="application/json", data="{}")
    assert resp.status_code == 400


@patch("src.parent.server._send_to_enclave")
def test_chat_success(mock_send, client):
    mock_send.return_value = {"status": "ok", "response": "Diversify your portfolio."}

    resp = client.post("/chat", json={"ciphertext": "dGVzdA=="})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["response"] == "Diversify your portfolio."


@patch("src.parent.server._send_to_enclave")
def test_chat_hybrid_forwards_all_fields(mock_send, client):
    mock_send.return_value = {"status": "ok", "response": "Consider index funds."}

    resp = client.post("/chat", json={
        "ciphertext": "dGVzdA==",
        "encrypted_data_key": "a2V5",
        "nonce": "bm9uY2U=",
    })
    assert resp.status_code == 200

    call_payload = mock_send.call_args[0][0]
    assert "encrypted_data_key" in call_payload
    assert "nonce" in call_payload


@patch("src.parent.server._send_to_enclave", side_effect=ConnectionRefusedError)
def test_chat_enclave_unavailable(mock_send, client):
    resp = client.post("/chat", json={"ciphertext": "dGVzdA=="})
    assert resp.status_code == 503
    data = resp.get_json()
    assert "Enclave unavailable" in data["error"]


@patch("src.parent.server._send_to_enclave")
def test_chat_enclave_error(mock_send, client):
    mock_send.return_value = {"status": "error", "error": "Decryption failed"}

    resp = client.post("/chat", json={"ciphertext": "dGVzdA=="})
    assert resp.status_code == 500
    data = resp.get_json()
    assert "Decryption failed" in data["error"]
