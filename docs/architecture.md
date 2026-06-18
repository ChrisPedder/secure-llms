# Architecture Document

## System Overview

This repository contains three independent sub-projects, each demonstrating a privacy-preserving ML technique on AWS. They share a common VPC and repository structure but are otherwise decoupled — each has its own CDK stack, Python dependencies, and entry point. The three sub-projects are:

1. **`federated/`** — Federated learning with Flower: simulated clients train a CNN on MNIST partitions, exchanging only gradient updates with a central server.
2. **`fhe/`** — Fully homomorphic encryption with Concrete-ML: a decision tree fraud detector trains and infers on encrypted financial data, compared against a plaintext baseline.
3. **`enclave/`** — Nitro Enclave chatbot: a web UI encrypts user messages client-side, sends ciphertext to an EC2-hosted enclave that decrypts via KMS attestation and calls Bedrock Claude for confidential financial advice.

## Architecture Diagram Descriptions

### Federated Learning Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  AWS (ECS Fargate) — or local machine                          │
│                                                                 │
│  ┌──────────────┐       gRPC (model updates only)              │
│  │ Flower Server │◄────────────────────────────────┐            │
│  │  (FedAvg)     │─────────────┐───────────┐       │            │
│  └──────────────┘             │           │       │            │
│         ▲                     ▼           ▼       ▼            │
│  ┌──────┴───────┐  ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│  │  Global Model │  │  Client 1   │ │  Client 2   │ │ Client 3 ││
│  │  (aggregated) │  │ MNIST 0-1-2 │ │ MNIST 3-4-5 │ │MNIST 6-9 ││
│  └──────────────┘  │ local train  │ │ local train  │ │local train││
│                     │ ▲           │ │ ▲           │ │ ▲        ││
│                     └─┼───────────┘ └─┼───────────┘ └─┼────────┘│
│                       │               │               │          │
│              ┌────────┴───────────────┴───────────────┴────────┐│
│              │  MNIST dataset (auto-downloaded, partitioned)    ││
│              │  ❌ Raw data never leaves the client             ││
│              └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

The Flower server orchestrates FedAvg rounds. Each client trains on its local MNIST partition and sends only model weight deltas. The server aggregates and distributes the updated global model. In local mode, Flower's simulation API runs all clients in a single process. In AWS mode, a single ECS Fargate task runs the simulation.

### FHE Fraud Detection Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  AWS (ECS Fargate) — or local machine                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    creditcard.csv                           │ │
│  │              (Kaggle, placed manually)                      │ │
│  └──────────┬─────────────────────────────┬───────────────────┘ │
│             │                             │                     │
│             ▼                             ▼                     │
│  ┌──────────────────┐          ┌──────────────────────────┐    │
│  │  Plaintext Path   │          │  FHE Path                │    │
│  │                   │          │                          │    │
│  │  sklearn Decision │          │  Concrete-ML Decision    │    │
│  │  Tree             │          │  Tree                    │    │
│  │  train → predict  │          │  compile → keygen →     │    │
│  │                   │          │  encrypt → predict →     │    │
│  │                   │          │  decrypt                 │    │
│  └────────┬─────────┘          └────────────┬─────────────┘    │
│           │                                  │                  │
│           ▼                                  ▼                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Comparison: accuracy, precision, recall, F1, wall time    │ │
│  │  🔒 In FHE path, the server only ever sees ciphertext      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

Both paths process the same preprocessed data. The plaintext path uses scikit-learn directly. The FHE path uses Concrete-ML's compatible API: the model is compiled to an FHE circuit, keys are generated, data is encrypted, inference runs on ciphertext, and results are decrypted. The comparison output shows the accuracy/performance trade-off.

### Nitro Enclave Chatbot Data Flow

```
┌──────────┐    HTTPS (RSA-OAEP ciphertext)    ┌──────────────────────────────────┐
│  Browser  │ ──────────────────────────────────►│  EC2 (enclave-enabled)           │
│           │                                    │                                  │
│  Web UI   │    ❌ Plaintext never sent          │  ┌────────────┐    vsock         │
│  encrypts │                                    │  │   Parent    │ ──────────────┐ │
│  with KMS │                                    │  │   (Flask)   │               │ │
│  public   │◄──────────────────────────────────│  │             │◄────────────┐ │ │
│  key      │    HTTPS (LLM response)            │  └─────┬──────┘             │ │ │
└──────────┘                                    │        │ vsock-proxy         │ │ │
                                                 │        │ ┌─KMS──────────┐   │ │ │
     ┌────────────┐                              │        │ │              │   │ │ │
     │  AWS KMS    │◄ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─│─┤  (proxied)   │   │ │ │
     │  RSA key    │  attestation-gated Decrypt   │        │ └──────────────┘   │ │ │
     │  pair       │                              │        │ ┌─Bedrock─────┐   │ │ │
     └────────────┘                              │        │ │              │   │ │ │
     ┌────────────┐                              │        │ │  (proxied)   │   │ │ │
     │  Bedrock    │◄ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─│─┤              │   │ │ │
     │  Claude     │                              │  ┌─────▼──┴──────────────┴───┘ │ │
     └────────────┘                              │  │     Nitro Enclave            │ │
                                                 │  │                              │ │
                                                 │  │  1. Receive ciphertext       │ │
                                                 │  │  2. KMS Decrypt (attested)   │ │
                                                 │  │  3. Build prompt + system msg│ │
                                                 │  │  4. Call Bedrock Claude       │ │
                                                 │  │  5. Return response           │ │
                                                 │  │  ❌ No persistent storage      │ │
                                                 │  │  ❌ No direct network access   │ │
                                                 │  └──────────────────────────────┘ │
                                                 └──────────────────────────────────┘

Auto-teardown: CloudWatch alarm on custom metric (last request timestamp).
If no requests for 30 min → Lambda stops EC2 instance.
```

The browser encrypts the user's message using the KMS RSA public key (fetched on page load). Ciphertext is sent to the parent EC2 instance, which forwards it to the enclave over vsock. The enclave calls KMS Decrypt (requiring attestation via PCR values) to recover the plaintext, prepends the system prompt, and calls Bedrock Claude through a vsock-proxy on the parent. The LLM response flows back through vsock to the parent and on to the browser. The enclave has no persistent storage and no direct network access.

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Application language | Python 3.10+ | Project constraint; ecosystem support for Flower, Concrete-ML, boto3, PyTorch |
| Federated learning framework | Flower 1.x | Mature, well-documented, built-in simulation mode, PyTorch integration |
| ML framework (federated) | PyTorch | Widely used for CNNs; clean Flower client integration |
| FHE library | Concrete-ML | Only production-ready FHE-ML library with a scikit-learn-compatible API |
| ML framework (FHE) | scikit-learn | Concrete-ML mirrors its API; decision trees are a native fit |
| Enclave application | Python + boto3 | Consistent language; boto3 for KMS and Bedrock API calls |
| Web UI | Vanilla HTML/CSS/JS | A single-page chatbot needs no framework; Web Crypto API for RSA encryption |
| Web server (parent) | Flask | Lightweight; sufficient for a demo API; serves static files and proxies vsock |
| IaC | AWS CDK (TypeScript) | Project constraint; type-safe, composable stacks, `DockerImageAsset` for container builds |
| CI/CD | GitHub Actions | Project decision; native to public GitHub repos |
| Compute (FL, FHE) | ECS Fargate | Serverless containers; no instance management; pay-per-second; auto-terminates |
| Compute (enclave) | EC2 `c5.xlarge` (enclave-enabled) | Smallest enclave-capable instance type; 4 vCPU / 8 GB is sufficient for the proxy + enclave workload |
| Encryption | AWS KMS (RSA asymmetric key pair) | Client-side encryption with public key; enclave-attested Decrypt for private key operations |
| LLM | Bedrock Claude | Project decision; managed API, no model hosting |
| Linting (Python) | Ruff | Fast, comprehensive, replaces flake8 + isort + pyflakes in a single tool |
| Linting (TypeScript) | ESLint | Standard for TypeScript CDK projects |
| Python dependency management | uv + pyproject.toml | Fast resolver, lockfile support, per-project virtual environments |
| Containerisation | Docker | Required for ECS Fargate tasks and Nitro Enclave images (EIF built from Dockerfile) |

## Component Breakdown

### Shared Infrastructure (`infra/`)

| Component | Responsibility | Interfaces | Dependencies |
|-----------|---------------|------------|--------------|
| SharedStack | Provisions VPC (2 AZs, public + private subnets, NAT gateway) and exports VPC ID / subnet IDs for sub-project stacks | CloudFormation exports: `SecureLlmsVpcId`, `SecureLlmsPublicSubnetIds`, `SecureLlmsPrivateSubnetIds` | None |

### Federated Learning (`federated/`)

| Component | Responsibility | Interfaces | Dependencies |
|-----------|---------------|------------|--------------|
| `src/model.py` | Defines the CNN architecture (2 conv layers + 2 FC layers) | `Net` class with standard PyTorch `forward()` | PyTorch |
| `src/data.py` | Downloads MNIST, partitions into N non-overlapping shards | `load_partition(partition_id, num_partitions) → DataLoader` | torchvision |
| `src/client.py` | Flower client: loads a partition, trains locally, returns updated weights | Implements `flwr.client.NumPyClient` | model.py, data.py |
| `src/server.py` | Flower server: FedAvg strategy, N rounds, evaluates global model | `start_server(num_rounds, num_clients)` | Flower |
| `src/run.py` | Entry point: parses args, runs simulation (local) or connects to AWS | CLI: `python run.py [--local] [--rounds N] [--clients N]` | server.py, client.py |
| `infra/lib/federated-stack.ts` | CDK stack: ECS Fargate task definition, CloudWatch log group | Imports shared VPC | SharedStack |

### FHE Fraud Detection (`fhe/`)

| Component | Responsibility | Interfaces | Dependencies |
|-----------|---------------|------------|--------------|
| `src/preprocess.py` | Loads `creditcard.csv`, undersamples majority class, train/test split | `load_and_preprocess(path) → (X_train, X_test, y_train, y_test)` | pandas, scikit-learn |
| `src/baseline.py` | Trains a plaintext sklearn `DecisionTreeClassifier`, reports metrics | `run_baseline(X_train, X_test, y_train, y_test) → MetricsDict` | scikit-learn |
| `src/encrypted.py` | Trains a Concrete-ML `DecisionTreeClassifier`, compiles to FHE circuit, infers on encrypted data | `run_encrypted(X_train, X_test, y_train, y_test) → MetricsDict` | Concrete-ML |
| `src/compare.py` | Runs both paths, prints a side-by-side comparison table | CLI: `python compare.py --data-path ./data/creditcard.csv` | baseline.py, encrypted.py |
| `src/run.py` | Entry point: validates dataset exists, orchestrates preprocessing + comparison | CLI: `python run.py [--local] [--data-path PATH]` | compare.py, preprocess.py |
| `infra/lib/fhe-stack.ts` | CDK stack: ECS Fargate task (4 vCPU, 8 GB), S3 bucket for results | Imports shared VPC | SharedStack |

### Nitro Enclave Chatbot (`enclave/`)

| Component | Responsibility | Interfaces | Dependencies |
|-----------|---------------|------------|--------------|
| `src/parent/server.py` | Flask app on parent EC2: serves web UI, proxies chat requests to enclave via vsock | `GET /` (UI), `GET /public-key` (KMS public key PEM), `POST /chat` (encrypted message) | Flask, socket (vsock) |
| `src/parent/static/` | Web UI: chat interface with client-side RSA-OAEP encryption using Web Crypto API | Browser loads `index.html`; `app.js` fetches public key and encrypts messages | None (vanilla JS) |
| `src/enclave/app.py` | Vsock server inside the enclave: receives ciphertext, calls KMS Decrypt (attested), builds prompt, calls Bedrock Claude | Vsock listener on port 5000; request/response as JSON over vsock | boto3 (patched for vsock-proxy), `aws-nitro-enclaves-sdk-python` |
| `src/enclave/Dockerfile` | Enclave image: Python app + dependencies, built into EIF via `nitro-cli` | `nitro-cli build-enclave --docker-uri ... --output-file enclave.eif` | Docker |
| `infra/lib/enclave-stack.ts` | CDK stack: EC2 `c5.xlarge` (enclave-enabled), KMS RSA key with attestation policy, security groups, CloudWatch alarm + Lambda for auto-teardown | Imports shared VPC; outputs instance public IP and KMS key ID | SharedStack |
| `infra/lib/teardown-lambda/` | Lambda function: stops the EC2 instance when triggered by CloudWatch alarm (30 min no activity) | Triggered by SNS topic from CloudWatch alarm | AWS SDK (EC2 StopInstances) |

## Data Model

### Federated Learning

No persistent data model. All state is in-memory during training.

| Entity | Attributes | Lifecycle |
|--------|-----------|-----------|
| MNIST partition | Subset of images + labels, partition ID, number of samples | Created at runtime from MNIST download; discarded after training |
| Model weights | PyTorch state dict (OrderedDict of tensors) | Initialised on server, distributed to clients, updated each round, final model optionally saved to disk |
| Training metrics | Round number, loss, accuracy (per-client and global) | Logged to stdout/CloudWatch per round |

### FHE Fraud Detection

| Entity | Attributes | Lifecycle |
|--------|-----------|-----------|
| Raw dataset | `creditcard.csv`: 30 features (V1-V28 + Time + Amount) + Class label | Manually downloaded by user; read-only input |
| Preprocessed data | NumPy arrays: X_train, X_test, y_train, y_test (after undersampling + split) | Created in memory during preprocessing |
| Plaintext model | sklearn `DecisionTreeClassifier` (fitted) | Created during baseline run; discarded after metrics are reported |
| FHE model | Concrete-ML `DecisionTreeClassifier` (compiled FHE circuit + keys) | Created during encrypted run; keys are ephemeral (not persisted) |
| Metrics | accuracy, precision, recall, F1, wall_time_seconds | Printed to stdout; optionally written to S3 as JSON |

### Nitro Enclave Chatbot

No persistent data model. The enclave is stateless by design.

| Entity | Attributes | Lifecycle |
|--------|-----------|-----------|
| Chat request | ciphertext (base64-encoded RSA-OAEP encrypted message) | Created in browser, sent to parent, forwarded to enclave, discarded after decryption |
| Decrypted prompt | system_prompt + user_message (plaintext) | Exists only inside enclave memory; never written to disk or logs |
| LLM response | response text (string) | Returned from Bedrock, sent back through vsock → parent → browser; not persisted |
| KMS public key | RSA public key in PEM format | Fetched from KMS on page load; cached in browser for session duration |

## API Contracts

### Enclave Chatbot HTTP API (Flask on parent EC2)

#### `GET /`

Serves the static web UI (index.html).

#### `GET /public-key`

Returns the KMS RSA public key for client-side encryption.

**Response:**
```json
{
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBI...\n-----END PUBLIC KEY-----"
}
```

#### `POST /chat`

Accepts an encrypted message and returns the LLM response.

**Request:**
```json
{
  "ciphertext": "<base64-encoded RSA-OAEP ciphertext>"
}
```

**Response:**
```json
{
  "response": "Based on your financial situation, I would recommend..."
}
```

**Error Response:**
```json
{
  "error": "Enclave unavailable"
}
```

### Enclave Vsock Protocol (internal, parent ↔ enclave)

Communication over vsock (AF_VSOCK), CID 16 (enclave), port 5000. Messages are newline-delimited JSON.

**Request (parent → enclave):**
```json
{
  "action": "decrypt_and_chat",
  "ciphertext": "<base64>"
}
```

**Response (enclave → parent):**
```json
{
  "status": "ok",
  "response": "..."
}
```

### Federated Learning and FHE

These sub-projects are batch jobs with CLI interfaces, not services. They have no HTTP APIs. Their interfaces are command-line arguments:

```
# Federated
python run.py --local --rounds 5 --clients 3
python run.py --rounds 5 --clients 3  # AWS mode (runs on Fargate)

# FHE
python run.py --local --data-path ./data/creditcard.csv
python run.py --data-path s3://bucket/creditcard.csv  # AWS mode
```

## Architectural Decision Records

### ADR-001: Flower Simulation Mode for AWS Deployment

- **Context:** The PRD requires deploying federated learning to AWS. Flower supports two modes: simulation (all clients in one process) and distributed (separate processes/machines per client). The user confirmed that simulated clients on a single machine are sufficient.
- **Options:** (A) Distributed Flower with separate ECS tasks per client and server. (B) Flower simulation in a single ECS task.
- **Decision:** Option B — single ECS Fargate task running Flower simulation.
- **Consequences:** Simpler infrastructure (one task vs. N+1), lower cost, faster startup. Loses the demonstration of real network-distributed FL, but this is explicitly out of MVP scope. If real distribution is needed later, the client/server code is already structured for it — only the deployment topology changes.

### ADR-002: KMS RSA Asymmetric Key for Client-Side Encryption

- **Context:** The PRD requires client-side encryption (NE-1) and KMS attestation-gated decryption (NE-6). The browser must encrypt without AWS credentials.
- **Options:** (A) KMS symmetric key with envelope encryption (requires the browser to call KMS Encrypt, needing AWS credentials). (B) KMS RSA asymmetric key — public key served to browser, Decrypt restricted to enclave. (C) Self-managed RSA key pair outside KMS.
- **Decision:** Option B — KMS RSA asymmetric key pair (`RSA_2048`, `RSAES_OAEP_SHA_256`).
- **Consequences:** The browser uses the Web Crypto API to encrypt with the public key — no AWS SDK or credentials needed client-side. KMS holds the private key and enforces the attestation policy on Decrypt. Trade-off: RSA-OAEP with 2048-bit key limits plaintext to ~190 bytes per encryption. For longer messages, the enclave will need to implement hybrid encryption (RSA-wrap an AES data key, AES-encrypt the message). This adds complexity but is a well-understood pattern.

### ADR-003: ECS Fargate for Batch ML Workloads

- **Context:** The federated and FHE sub-projects need cloud compute for training/inference. They are batch jobs, not long-running services.
- **Options:** (A) EC2 instances with startup scripts. (B) ECS Fargate tasks. (C) AWS Batch with Fargate compute environment.
- **Decision:** Option B — ECS Fargate.
- **Consequences:** No instance management, pay-per-second, auto-terminates when the task exits. CDK's `DockerImageAsset` handles ECR image builds automatically. AWS Batch would add another abstraction layer without clear benefit for a demo. EC2 would require manual lifecycle management.

### ADR-004: Per-Sub-Project CDK Apps with Shared Base Stack

- **Context:** The PRD requires independent deployment and teardown per sub-project (NFR-4), plus shared infrastructure (RF-2).
- **Options:** (A) Single CDK app with multiple stacks. (B) Separate CDK apps per sub-project, with a shared app for base infra.
- **Decision:** Option B — each sub-project has its own CDK app under `<subproject>/infra/`, plus `infra/` at root for the shared stack. Sub-project stacks import shared resources via CloudFormation exports.
- **Consequences:** `cdk deploy` and `cdk destroy` work independently per sub-project. The shared stack must be deployed first and destroyed last. Cross-stack references use `Fn.importValue`, which is simple but means the shared stack can't be destroyed while any sub-project stack exists.

### ADR-005: uv for Python Dependency Management

- **Context:** Each sub-project needs isolated Python dependencies (RF-3). The project is public and should use modern, well-supported tooling.
- **Options:** (A) pip + requirements.txt. (B) Poetry. (C) uv + pyproject.toml.
- **Decision:** Option C — uv with pyproject.toml and uv.lock per sub-project.
- **Consequences:** Fast installs (10-100x faster than pip), deterministic lockfiles, standard pyproject.toml format. uv is newer than Poetry but rapidly maturing and simpler (no separate lock command, no config file beyond pyproject.toml). Each sub-project has its own virtualenv created by `uv sync`.

## Coding Standards

### Python

- **Formatter/Linter:** Ruff (replaces black + flake8 + isort). Configuration in root `pyproject.toml` under `[tool.ruff]`.
- **Type hints:** Use type hints on all function signatures. No runtime type checking (no Pydantic for internal code; use it only for API request/response models in Flask if needed).
- **Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants.
- **Imports:** Sorted by ruff (isort-compatible). Standard library → third-party → local.
- **Error handling:** Fail fast with clear error messages at system boundaries (missing dataset file, missing AWS credentials, enclave connection refused). No defensive try/except around internal code.
- **Testing:** pytest. Unit tests for data processing and model utilities. No mocking of AWS services in unit tests — integration tests against real AWS are out of MVP scope but the structure should support adding them.

### TypeScript (CDK)

- **Formatter/Linter:** ESLint + Prettier. Configuration in each `infra/` directory.
- **Naming:** camelCase for variables/functions, PascalCase for classes/stacks/constructs.
- **Stack outputs:** Always output resource identifiers (VPC ID, task ARN, instance IP) as `CfnOutput` for discoverability.
- **Tagging:** All resources tagged with `Project: secure-llms` and `SubProject: federated|fhe|enclave`.

### General

- **No comments** unless the "why" is non-obvious.
- **No TODOs** in committed code — track in issues instead.
- **Secrets:** Never committed. Use environment variables or AWS Secrets Manager. `.gitignore` includes `*.env`, `credentials*`, `*.pem`, `*.key`.

## File Structure Conventions

```
secure-llms/
├── CLAUDE.md
├── README.md                       # Project overview + links to sub-projects
├── pyproject.toml                   # Root: ruff config only (no dependencies)
├── .github/
│   └── workflows/
│       ├── ci.yml                   # Lint + test for all sub-projects
│       └── enclave-teardown.yml     # Scheduled/manual teardown check
├── infra/                           # Shared CDK app
│   ├── package.json
│   ├── tsconfig.json
│   ├── bin/
│   │   └── app.ts                   # CDK app entry point
│   └── lib/
│       └── shared-stack.ts          # VPC, CloudFormation exports
│
├── federated/
│   ├── README.md
│   ├── pyproject.toml               # Flower, PyTorch, torchvision
│   ├── uv.lock
│   ├── Dockerfile                   # For ECS Fargate
│   ├── src/
│   │   ├── __init__.py
│   │   ├── model.py                 # CNN definition
│   │   ├── data.py                  # MNIST download + partition
│   │   ├── client.py                # Flower NumPyClient
│   │   ├── server.py                # Flower server + FedAvg
│   │   └── run.py                   # CLI entry point
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_model.py
│   │   └── test_data.py
│   └── infra/
│       ├── package.json
│       ├── tsconfig.json
│       ├── bin/
│       │   └── app.ts
│       └── lib/
│           └── federated-stack.ts
│
├── fhe/
│   ├── README.md
│   ├── pyproject.toml               # Concrete-ML, scikit-learn, pandas
│   ├── uv.lock
│   ├── Dockerfile                   # For ECS Fargate
│   ├── data/
│   │   └── .gitkeep                 # User places creditcard.csv here
│   ├── src/
│   │   ├── __init__.py
│   │   ├── preprocess.py            # Load CSV, balance, split
│   │   ├── baseline.py              # sklearn decision tree
│   │   ├── encrypted.py             # Concrete-ML FHE decision tree
│   │   ├── compare.py               # Run both + comparison table
│   │   └── run.py                   # CLI entry point
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_preprocess.py
│   │   └── test_baseline.py
│   └── infra/
│       ├── package.json
│       ├── tsconfig.json
│       ├── bin/
│       │   └── app.ts
│       └── lib/
│           └── fhe-stack.ts
│
├── enclave/
│   ├── README.md
│   ├── pyproject.toml               # Flask, boto3
│   ├── uv.lock
│   ├── src/
│   │   ├── parent/
│   │   │   ├── __init__.py
│   │   │   ├── server.py            # Flask app (serves UI, proxies vsock)
│   │   │   └── static/
│   │   │       ├── index.html       # Chat UI
│   │   │       ├── style.css
│   │   │       └── app.js           # Web Crypto encryption + chat
│   │   └── enclave/
│   │       ├── app.py               # Vsock server (KMS decrypt + Bedrock)
│   │       ├── Dockerfile           # Built into EIF
│   │       └── requirements.txt     # Enclave has its own deps (minimal)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_server.py
│   └── infra/
│       ├── package.json
│       ├── tsconfig.json
│       ├── bin/
│       │   └── app.ts
│       └── lib/
│           ├── enclave-stack.ts     # EC2, KMS, SG, CloudWatch, Lambda
│           └── teardown-lambda/
│               └── index.ts         # Lambda: stop EC2 on alarm
│
└── docs/
    ├── project-brief.md
    ├── prd.md
    └── architecture.md
```

### Conventions

- Each sub-project is self-contained: its own `pyproject.toml`, `Dockerfile`, `infra/`, `tests/`, and `README.md`.
- Python source lives under `src/` with an `__init__.py` for package imports.
- CDK apps follow the standard `bin/app.ts` + `lib/*-stack.ts` pattern.
- The `data/` directory in `fhe/` is `.gitignore`d (except `.gitkeep`) — the user must supply the dataset.
- No shared Python code between sub-projects — each is independent.

## Technical Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Concrete-ML API breaking changes** — Concrete-ML is pre-1.0 and evolving | Medium | Medium | Pin exact version in `pyproject.toml` with `uv.lock`; document tested version in README |
| **RSA plaintext size limit** — RSA-OAEP with 2048-bit key limits encryption to ~190 bytes | High | Medium | Implement hybrid encryption: RSA-wrap a random AES-256 data key, AES-GCM encrypt the message. Document in ADR-002 |
| **Nitro Enclave vsock-proxy for Bedrock** — The standard `vsock-proxy` is maintained by AWS for KMS but Bedrock proxying may need custom configuration | Medium | High | Test vsock-proxy with Bedrock endpoints early; fall back to a custom TCP-over-vsock proxy if needed |
| **Enclave EIF build toolchain** — Building enclave images (EIF) requires `nitro-cli` which only runs on Amazon Linux on Nitro-based instances | High | Medium | EIF must be built on an EC2 instance (or in CI on a Nitro instance); cannot build locally on macOS. Document this in README; provide a build script that SSHs to the instance |
| **Auto-teardown reliability** — CloudWatch custom metrics require the parent instance to publish; if the instance crashes, the metric stops and the alarm enters INSUFFICIENT_DATA | Medium | Medium | Treat INSUFFICIENT_DATA as alarm state (trigger teardown); add a fallback GitHub Actions scheduled workflow that checks instance state |
| **Fargate task timeout** — FHE operations on Concrete-ML can be slow; Fargate tasks have a max runtime of ~24 hours but may hit memory limits | Low | Medium | Allocate 4 vCPU / 8 GB for the FHE task; monitor memory usage in CloudWatch; document expected runtime in README |
| **Bedrock model access** — Claude on Bedrock requires explicit model access enablement per region | Medium | High | CDK stack fails fast if Bedrock is unreachable; README documents the model access request process with screenshots |
