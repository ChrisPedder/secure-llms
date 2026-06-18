# Enclave Parent Server and Web UI

**Epic:** Nitro Enclave Secure Chatbot (Bedrock Claude)

**Refs:** NE-1, NE-3, NE-4

## User Story

As a user, I want a web-based chat interface for confidential financial advice where my messages are encrypted in the browser before being sent so that my sensitive financial queries are never exposed in plaintext outside my browser.

## Acceptance Criteria

- [x] `enclave/src/parent/server.py` is a Flask app that serves the web UI and proxies chat requests to the enclave via vsock
- [x] `GET /` serves the chat UI from `static/`
- [x] `GET /public-key` returns the KMS RSA public key in PEM format
- [x] `POST /chat` accepts `{"ciphertext": "<base64>"}`, forwards to enclave via vsock, and returns `{"response": "..."}`
- [x] The web UI (`index.html`, `style.css`, `app.js`) presents a chat interface themed for confidential financial advice
- [x] `app.js` fetches the public key on page load and encrypts all user messages client-side using Web Crypto API (RSA-OAEP)
- [x] For messages exceeding RSA limits, `app.js` implements hybrid encryption: generate AES-256 key, RSA-wrap it, AES-GCM encrypt the message, send both
- [x] Plaintext user messages are never sent over the network
- [x] Error states (enclave unavailable, encryption failure) show clear messages in the UI
- [x] Unit tests exist for the Flask routes (mocking vsock) — 9 tests

## Technical Notes

- See architecture.md: API Contracts, Enclave Vsock Protocol, ADR-002
- The parent communicates with the enclave over AF_VSOCK (CID 16, port 5000)
- Web Crypto API: `crypto.subtle.importKey()` for the RSA public key, `crypto.subtle.encrypt()` for RSA-OAEP
- Hybrid encryption in JS: `crypto.subtle.generateKey()` for AES-256-GCM, encrypt message, RSA-wrap the AES key
- The parent also runs `vsock-proxy` processes for KMS and Bedrock endpoints (started as background processes or via systemd)
- Financial advice theme: clean, professional styling; placeholder logo; dark blue / white colour scheme

## Implementation Subtasks

- [x] Implement Flask app in `server.py` with routes
- [x] Implement vsock client helper (connect to enclave CID/port, send/receive JSON)
- [x] Build chat UI in `index.html` + `style.css`
- [x] Implement client-side encryption in `app.js` (RSA-OAEP + hybrid AES-GCM)
- [x] Add error handling for enclave unavailability
- [x] Write unit tests for Flask routes (9 tests)

## Status

Todo | In Progress | In Review | **Done**
