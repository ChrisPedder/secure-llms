# Nitro Enclave Secure Chatbot

Privacy-preserving LLM inference -- a web UI encrypts user messages client-side using a KMS RSA public key, sends ciphertext to an AWS Nitro Enclave that decrypts via KMS attestation and calls Bedrock Claude. The plaintext message never exists outside the user's browser and the enclave's sealed memory.

## Architecture

```
 TRUST BOUNDARY: Browser                TRUST BOUNDARY: Nitro Enclave
 ┌─────────────────────┐                ┌──────────────────────────────┐
 │  Web UI (app.js)    │                │  Enclave App (app.py)        │
 │                     │                │                              │
 │  1. Fetch KMS       │                │  1. Receive ciphertext       │
 │     public key      │                │  2. KMS Decrypt (attested)   │
 │  2. Encrypt message │                │  3. Build prompt + system    │
 │     (RSA-OAEP or    │   ciphertext   │  4. Call Bedrock Claude      │
 │      hybrid AES)    │ ──────────────►│  5. Return LLM response      │
 │  3. Send ciphertext │                │                              │
 │                     │◄──────────────│  No disk. No logs.           │
 │  Plaintext never    │   response     │  No direct network access.   │
 │  leaves browser     │                └──────────┬───────────────────┘
 └─────────────────────┘                           │ vsock
                                        ┌──────────┴───────────────────┐
 ┌─────────────────────┐                │  Parent EC2                  │
 │  AWS KMS            │◄───────────────│  Flask server (server.py)    │
 │  RSA-2048 key       │  vsock-proxy   │  vsock-proxy → KMS           │
 │  (attestation-gated │                │  vsock-proxy → Bedrock       │
 │   Decrypt)          │                └──────────────────────────────┘
 └─────────────────────┘
 ┌─────────────────────┐
 │  Bedrock Claude     │◄─── proxied through vsock-proxy on parent
 └─────────────────────┘

 Encryption boundaries:
   Browser ──[RSA-OAEP ciphertext]──► Parent ──[ciphertext, untouched]──► Enclave
   Only the enclave can decrypt (KMS attestation required).
```

### Auto-Teardown

The enclave instance auto-stops after 30 minutes of inactivity:

1. Parent server publishes a `LastRequestTimestamp` CloudWatch metric on each `/chat` request
2. A CloudWatch alarm triggers when no data points arrive for 30 minutes
3. The alarm fires an SNS topic that invokes a Lambda function
4. The Lambda stops the EC2 instance
5. A GitHub Actions workflow runs every 6 hours as a safety-net fallback

## Cost Warning

The enclave runs on a `c5.xlarge` instance (~$0.17/hour). The auto-teardown mechanism stops the instance after 30 minutes of idle time, but you are responsible for verifying it works and for running `cdk destroy` when done.

**Always run `cdk destroy` when you are finished testing.**

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Node.js 18+ and npm
- AWS CLI v2, configured with credentials
- **Bedrock model access**: Request access to Claude in the AWS console (Bedrock > Model access > Request access)

## AWS Deployment

This sub-project requires AWS deployment -- it cannot run fully locally (Nitro Enclaves require EC2 Nitro hardware).

### Deploy

```bash
# Deploy shared VPC first (if not already done)
cd infra && npx cdk deploy && cd ..

# Deploy enclave stack
cd enclave/infra
npm install
npx cdk deploy
```

Note the outputs: `InstancePublicIp` and `KmsKeyId`.

### Use

1. SSH into the instance (via SSM Session Manager) to verify the enclave is running:
   ```bash
   aws ssm start-session --target <InstanceId>
   nitro-cli describe-enclaves
   ```

2. Open `http://<InstancePublicIp>:8080` in your browser

3. The UI will fetch the encryption key and show "Encryption ready"

4. Type a financial question -- it is encrypted in your browser before sending

### Local Development (Tests Only)

```bash
cd enclave
uv sync --dev
uv run pytest tests/ -v
```

The tests mock vsock and AWS calls, so they run without any AWS infrastructure.

## Clean Up

```bash
cd enclave/infra && npx cdk destroy
```

This removes the EC2 instance, KMS key, CloudWatch alarm, Lambda, and all associated resources.
