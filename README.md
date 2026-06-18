# Secure ML/AI on AWS

Three runnable sub-projects exploring privacy-preserving approaches to machine learning and AI inference on AWS.

| Approach | Sub-project | What it demonstrates |
|----------|-------------|---------------------|
| **Federated Learning** | [`federated/`](federated/) | Multiple simulated clients train a CNN on local MNIST partitions, exchanging only weight updates via Flower |
| **Fully Homomorphic Encryption** | [`fhe/`](fhe/) | A decision tree fraud detector trains and infers on encrypted financial data using Concrete-ML |
| **Nitro Enclave Inference** | [`enclave/`](enclave/) | Browser-encrypted messages are decrypted inside a Nitro Enclave via KMS attestation, then sent to Bedrock Claude |

## Architecture

```
secure-llms/
  federated/      Flower + PyTorch, MNIST classification
  fhe/            Concrete-ML, Kaggle credit card fraud detection
  enclave/        Nitro Enclave + KMS + Bedrock Claude chatbot
  infra/          Shared CDK stack (VPC)
  docs/           Architecture, PRD, stories
```

Each sub-project runs independently with its own Python environment, Dockerfile, and CDK stack. A shared CDK stack provisions the VPC used by all three.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ and npm (for CDK)
- AWS CLI v2, configured with credentials
- Docker (for building container images)
- An AWS account with Bedrock model access (enclave sub-project only)

## Quick Start

```bash
# Install shared CDK dependencies
cd infra && npm install && cd ..

# Deploy shared VPC (required before sub-project stacks)
cd infra && npx cdk deploy && cd ..

# Then pick a sub-project:
cd federated/   # or fhe/ or enclave/
```

See each sub-project's README for detailed setup and run instructions.

## Infrastructure

All infrastructure is defined as CDK TypeScript stacks:

| Stack | Directory | Resources |
|-------|-----------|-----------|
| `SecureLlmsShared` | `infra/` | VPC with public + private subnets, NAT gateway |
| `SecureLlmsFederated` | `federated/infra/` | ECS Fargate cluster + task definition, CloudWatch logs |
| `SecureLlmsFhe` | `fhe/infra/` | ECS Fargate cluster + task, S3 bucket for data |
| `SecureLlmsEnclave` | `enclave/infra/` | EC2 c5.xlarge (Nitro), KMS RSA key, auto-teardown alarm + Lambda |

Deploy order: shared stack first, then any sub-project stack.

## Clean Up

```bash
# Destroy sub-project stacks first
cd federated/infra && npx cdk destroy && cd ../..
cd fhe/infra && npx cdk destroy && cd ../..
cd enclave/infra && npx cdk destroy && cd ../..

# Then the shared stack
cd infra && npx cdk destroy && cd ..
```

## CI/CD

GitHub Actions workflows:
- **`ci.yml`** — Lints Python (ruff) and TypeScript (tsc + eslint), runs pytest for each sub-project
- **`deploy.yml`** — Auto-deploys shared, federated, and FHE stacks on push to main
- **`enclave-session.yml`** — Manual trigger to deploy the enclave stack (run via `gh workflow run enclave-session.yml`)
- **`fhe-train.yml`** — Manual trigger to train the FHE model (downloads data from S3, trains, uploads model back)
- **`enclave-session.yml`** — Manual trigger to deploy the enclave stack (run via `gh workflow run enclave-session.yml`)
- **`enclave-teardown.yml`** — Runs hourly; stops idle instances, then `cdk destroy`s the stack once stopped
