# Nitro Enclave Application

**Epic:** Nitro Enclave Secure Chatbot (Bedrock Claude)

**Refs:** NE-2, NE-6

## User Story

As a practitioner, I want an enclave application that decrypts user input via KMS attestation and calls Bedrock Claude so that I can understand how Nitro Enclaves protect data during LLM inference.

## Acceptance Criteria

- [x] `enclave/src/enclave/app.py` runs a vsock server (AF_VSOCK, port 5000) inside the enclave
- [x] The enclave app receives JSON requests with base64-encoded ciphertext
- [x] It calls KMS Decrypt through the vsock-proxy, presenting the enclave attestation document
- [x] For messages exceeding RSA plaintext limits (~190 bytes), hybrid decryption is used: RSA-unwrap an AES data key, then AES-GCM decrypt the message
- [x] The decrypted user message is combined with a system prompt for "confidential financial advice"
- [x] The combined prompt is sent to Bedrock Claude via vsock-proxy
- [x] The LLM response is returned as JSON over vsock
- [x] No user data is written to disk or logs inside the enclave
- [x] `enclave/src/enclave/Dockerfile` builds a minimal image suitable for EIF conversion
- [x] `enclave/src/enclave/requirements.txt` lists only necessary dependencies

## Technical Notes

- See architecture.md: Nitro Enclave Chatbot Data Flow, ADR-002, Component Breakdown
- The enclave has no direct network access — all AWS API calls go through `vsock-proxy` on the parent
- vsock-proxy configuration: CID 3 (parent), separate ports for KMS and Bedrock endpoints
- boto3 must be configured to route through the vsock proxy (custom endpoint URLs or HTTP adapter patching)
- The `aws-nitro-enclaves-sdk-python` package provides KMS integration with attestation
- System prompt example: "You are a confidential financial advisor. Provide helpful, accurate financial guidance. Never disclose that you are operating inside a secure enclave."
- Bedrock Claude model ID: use the latest available Claude model in the target region

## Implementation Subtasks

- [x] Implement vsock server in `app.py`
- [x] Implement KMS Decrypt with attestation document (with fallback for non-enclave testing)
- [x] Implement hybrid decryption (RSA + AES-GCM) for long messages
- [x] Implement Bedrock Claude call via vsock-proxy
- [x] Implement system prompt construction
- [x] Write `Dockerfile` for enclave image
- [x] Write `requirements.txt`
- [x] Write unit tests (4 tests: direct RSA, hybrid decrypt, unknown action, full flow)

## Status

Todo | In Progress | In Review | **Done**
