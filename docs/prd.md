# Product Requirements Document

## Overview

This PRD translates the approved [project brief](project-brief.md) into actionable requirements for a monorepo containing three privacy-preserving ML sub-projects on AWS. Each sub-project demonstrates a distinct technique — federated learning, fully homomorphic encryption, and trusted execution environments — as a self-contained, deployable example. The repository targets hands-on learning for the owner while serving as a clean, public reference for the broader community.

## Functional Requirements

### Epic 1: Repository Foundation

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| RF-1 | Monorepo structure with three sub-project directories (`federated/`, `fhe/`, `enclave/`) and a shared root | Running `ls` at root shows `federated/`, `fhe/`, `enclave/`, each with its own `README.md`, `src/`, and `infra/` directory |
| RF-2 | Shared CDK infrastructure bootstrap (VPC, IAM baseline) in a root-level `infra/` directory | `cdk deploy` from root `infra/` provisions a VPC and shared IAM roles; sub-project stacks reference these via exports |
| RF-3 | Python dependency management per sub-project using a standard tool (e.g. `pyproject.toml` + `uv` or `requirements.txt`) | Each sub-project can install its Python dependencies in isolation without conflicting with the others |
| RF-4 | GitHub Actions CI pipeline that lints and tests each sub-project independently | A push to `main` triggers lint and test jobs for all three sub-projects; each job passes or fails independently |

### Epic 2: Federated Learning (Flower + MNIST)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FL-1 | Flower-based federated learning server that coordinates training rounds | Server starts, accepts client connections, and orchestrates at least 3 rounds of federated averaging |
| FL-2 | Simulated Flower clients (minimum 3) that train on local MNIST partitions and send gradient updates | Each client loads a distinct partition of MNIST, trains locally, and sends model updates to the server; no raw data leaves the client |
| FL-3 | MNIST dataset auto-download and partitioning across simulated clients | Running the training script automatically downloads MNIST (if not cached) and splits it into N non-overlapping partitions |
| FL-4 | Training produces a usable global model with logged accuracy | After federated training completes, the aggregated model achieves ≥90% accuracy on the MNIST test set; accuracy is printed to stdout |
| FL-5 | CDK stack deploys the federated training environment to AWS (e.g. ECS tasks or EC2 instances) | `cdk deploy` provisions compute for the server and clients; a single command starts a federated training run on AWS |
| FL-6 | Local-mode execution for development without AWS deployment | A `--local` flag or separate script runs the full federated training loop on the developer's machine without requiring AWS resources |

### Epic 3: FHE Fraud Detection (Concrete-ML)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FHE-1 | Data preprocessing pipeline for the Kaggle credit card fraud dataset | Script reads `creditcard.csv`, handles class imbalance (e.g. undersampling), splits into train/test, and outputs preprocessed arrays |
| FHE-2 | Plaintext baseline: train a scikit-learn decision tree and report accuracy, precision, recall, F1 | Running the baseline script prints classification metrics; serves as the comparison point for the FHE model |
| FHE-3 | Concrete-ML encrypted model: train a decision tree on encrypted data using Concrete-ML | The Concrete-ML model compiles, generates keys, and trains/infers on FHE-encrypted data; script prints the same metrics as FHE-2 |
| FHE-4 | Performance comparison output: plaintext vs. FHE accuracy and execution time | A summary table or log comparing accuracy and wall-clock time for plaintext vs. FHE inference is printed after both runs complete |
| FHE-5 | CDK stack deploys the FHE training/inference environment to AWS | `cdk deploy` provisions compute (e.g. an EC2 instance or ECS task) that runs the FHE pipeline; results are retrievable from CloudWatch logs or S3 |
| FHE-6 | Local-mode execution for development without AWS deployment | The full FHE pipeline can run locally given `creditcard.csv` is present; no AWS resources required |
| FHE-7 | Setup instructions for obtaining the Kaggle dataset | README includes step-by-step instructions for downloading `creditcard.csv` from Kaggle and placing it in the expected location |

### Epic 4: Nitro Enclave Secure Chatbot (Bedrock Claude)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NE-1 | Client-side encryption: user input is encrypted before leaving the client | The web UI encrypts the user's message using a public key before sending it to the backend; plaintext is never transmitted over the network |
| NE-2 | Nitro Enclave application that decrypts input, constructs a prompt, and calls Bedrock Claude | Inside the enclave: received ciphertext is decrypted using KMS-attested keys, a system prompt for "confidential financial advice" is prepended, and the combined prompt is sent to Bedrock Claude |
| NE-3 | Enclave returns the LLM response to the client | The Bedrock response is sent back to the client and displayed in the web UI; the enclave does not persist any user data |
| NE-4 | Minimal web UI themed as a confidential financial advice chatbot | A single-page web app with a chat interface, styled for financial advice, allows the user to type messages and see responses |
| NE-5 | CDK stack deploys the enclave host (EC2 `.metal` or enclave-enabled), networking, and KMS key | `cdk deploy` provisions the enclave-capable instance, security groups, KMS key with enclave attestation policy, and API Gateway or ALB for the web UI |
| NE-6 | KMS key policy restricts decryption to the enclave's attestation document (PCR values) | The KMS key policy allows `kms:Decrypt` only when the request originates from an enclave with the expected PCR0/PCR1/PCR2 values |
| NE-7 | Auto-teardown after 30 minutes of inactivity | A CloudWatch alarm or Lambda monitors the last request timestamp; if no activity for 30 minutes, the EC2 instance is stopped and the stack's expensive resources are scaled to zero; a GitHub Actions workflow can also trigger teardown |

### Epic 5: Documentation and Developer Experience

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| DX-1 | Root README with project overview, architecture summary, and links to sub-project READMEs | Root `README.md` explains the purpose of the repo, lists the three approaches with one-sentence descriptions, and links to each sub-project |
| DX-2 | Per-sub-project README with setup, deploy, and run instructions | Each sub-project `README.md` includes: prerequisites, install steps, local run instructions, AWS deploy instructions, and expected output |
| DX-3 | Architecture diagram per sub-project showing data flow and encryption boundaries | Each sub-project README includes (or links to) a diagram showing what is encrypted, where encryption/decryption occurs, and what crosses trust boundaries |

## Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-1 | **Security** | No plaintext sensitive data crosses trust boundaries in any sub-project | Verified by architecture review; enclave uses KMS attestation |
| NFR-2 | **Security** | No secrets (AWS keys, API keys) committed to the repository | `.gitignore` covers credential files; CI checks for secret patterns |
| NFR-3 | **Cost** | Nitro Enclave infrastructure auto-terminates after 30 min of inactivity | CloudWatch metric + alarm/Lambda confirmed in integration test |
| NFR-4 | **Cost** | All CDK stacks are individually destroyable with `cdk destroy` | Each stack tears down cleanly with no orphaned resources |
| NFR-5 | **Performance** | Federated training completes within 30 minutes on AWS (3 clients, 5 rounds) | Timed in CI or manual run |
| NFR-6 | **Performance** | FHE inference on a single sample completes within 60 seconds | Timed in the comparison output (FHE-4) |
| NFR-7 | **Portability** | All Python code runs on Python 3.10+ | CI tests against Python 3.10 |
| NFR-8 | **Readability** | Code passes linting (ruff or flake8) with no exceptions | CI lint job passes on every push |
| NFR-9 | **Readability** | CDK code passes `eslint` with no exceptions | CI lint job passes on every push |

## MVP Scope

| Feature / Capability | In MVP | Out of MVP |
|----------------------|--------|------------|
| Federated learning with Flower on MNIST (local + AWS) | Yes | |
| FHE fraud detection with Concrete-ML (local + AWS) | Yes | |
| Nitro Enclave chatbot with Bedrock Claude (AWS only) | Yes | |
| Local-mode execution for federated and FHE sub-projects | Yes | |
| Minimal web UI for enclave chatbot | Yes | |
| Auto-teardown of enclave infra after 30 min inactivity | Yes | |
| GitHub Actions CI (lint + test) | Yes | |
| Per-sub-project README with setup/deploy/run instructions | Yes | |
| Architecture diagrams | Yes | |
| Multi-region deployment | | Out |
| Production-grade auth/authz on the chatbot UI | | Out |
| Deep learning models under FHE | | Out |
| Real multi-node federated learning across AWS accounts | | Out |
| Automated performance benchmarking suite | | Out |
| Terraform or Pulumi alternatives to CDK | | Out |
| Mobile or desktop client for the chatbot | | Out |
| Continuous training / model versioning | | Out |

## Prioritised Epics

| Priority | Epic | Rationale |
|----------|------|-----------|
| **Must** | Epic 1: Repository Foundation | All sub-projects depend on the shared repo structure, CI, and base infra |
| **Must** | Epic 2: Federated Learning | Core sub-project; well-understood technique; unblocks end-to-end validation of the repo pattern |
| **Must** | Epic 3: FHE Fraud Detection | Core sub-project; validates the FHE workflow and Concrete-ML integration |
| **Must** | Epic 4: Nitro Enclave Chatbot | Core sub-project; most complex AWS integration; validates the enclave + Bedrock pattern |
| **Must** | Epic 5: Documentation and DX | The repo is public — readability and setup instructions are essential, not optional |

## Risks and Dependencies

| Risk / Dependency | Likelihood | Impact | Mitigation |
|-------------------|------------|--------|------------|
| **Concrete-ML version compatibility** — Concrete-ML is evolving rapidly; APIs may change between versions | Medium | Medium | Pin the Concrete-ML version in `pyproject.toml`; document the tested version |
| **Nitro Enclave instance availability** — `.metal` or enclave-enabled instances may not be available in all regions or may have capacity limits | Medium | High | Document supported regions; CDK stack parameterises instance type and region |
| **Kaggle dataset download** — Requires manual step with Kaggle authentication | Low | Low | Clear instructions in README; a validation script checks the file exists before training |
| **Bedrock model access** — Claude on Bedrock requires model access to be enabled in the AWS account | Medium | High | Document the Bedrock model access request process; fail fast with a clear error if access is missing |
| **Enclave auto-teardown reliability** — CloudWatch/Lambda-based teardown may miss edge cases (e.g. alarm in INSUFFICIENT_DATA state) | Medium | Medium | Integration test that deploys, idles, and verifies teardown; fallback cron-based check |
| **Cost overruns** — Nitro Enclave instances are expensive if teardown fails | Low | High | Budget alert in CDK stack; auto-teardown is a Must requirement; `cdk destroy` documented as manual fallback |

## Glossary

| Term | Definition |
|------|------------|
| **Federated Learning** | A machine learning approach where multiple clients collaboratively train a model by sharing only model updates (gradients), not raw data |
| **FHE (Fully Homomorphic Encryption)** | An encryption scheme that allows computation on ciphertext, producing results that, when decrypted, match the result of operations on the plaintext |
| **Concrete-ML** | An open-source library by Zama that provides ML model APIs (scikit-learn compatible) that operate on FHE-encrypted data |
| **Flower** | An open-source federated learning framework that supports simulating and deploying federated workloads across multiple clients |
| **Nitro Enclave** | An AWS isolation technology that creates a hardened, attested execution environment on EC2 instances, with no persistent storage, no network access, and cryptographic attestation |
| **Bedrock** | AWS's managed service for accessing foundation models (including Claude) via API |
| **KMS Attestation** | A feature where AWS KMS validates an enclave's attestation document (PCR values) before allowing cryptographic operations, ensuring only verified code can decrypt data |
| **PCR (Platform Configuration Register)** | Hash values that uniquely identify the code and configuration running inside a Nitro Enclave; used in KMS key policies to restrict access |
| **CDK (Cloud Development Kit)** | An AWS IaC framework that lets you define cloud resources in programming languages (TypeScript in this project) |
| **MoSCoW** | A prioritisation method: Must have, Should have, Could have, Won't have |
