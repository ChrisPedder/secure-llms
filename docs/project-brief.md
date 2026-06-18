# Project Brief

## Executive Summary

This project explores three distinct approaches to privacy-preserving machine learning on AWS, implemented as runnable sub-projects in a single repository. The three approaches are: federated learning (training without sharing raw data), fully homomorphic encryption via Concrete-ML (computing on encrypted data), and AWS Nitro Enclaves for secure LLM inference via Bedrock. Each sub-project is a self-contained, deployable example built in Python with AWS CDK (TypeScript) infrastructure, intended as a hands-on learning resource that is also clean and legible enough for public consumption.

## Problem Statement

Machine learning workloads increasingly involve sensitive data — medical records, financial transactions, personal communications — yet standard ML pipelines require data to be available in plaintext to the training or inference infrastructure. This creates a tension between leveraging cloud compute and maintaining data privacy. Organisations need practical, deployable patterns for secure ML, but most educational resources stop at theory or toy local demos. There is a gap in complete, AWS-deployable reference implementations that a practitioner can run end-to-end to understand the trade-offs of each approach.

## Target Users

### Primary: The repository owner (Chris)

A practitioner exploring privacy-preserving ML techniques through hands-on implementation. Wants to build, deploy, and test each approach on real AWS infrastructure to develop practical understanding beyond theory.

### Secondary: Public repository visitors

Engineers and researchers browsing the public repo who want to understand how these techniques work in practice. They may not deploy the examples themselves, but should be able to follow the code, architecture, and documentation to learn from them.

## User Needs and Pain Points

### Primary user

- **Need:** Hands-on, runnable implementations of three secure ML approaches on AWS.
- **Need:** Each sub-project should be independently deployable with clear instructions.
- **Need:** Cost-conscious infrastructure — especially for Nitro Enclaves, which require expensive instance types.
- **Pain point:** Existing tutorials and examples rarely go beyond local execution; deploying to real cloud infrastructure with IaC is poorly covered.
- **Pain point:** Comparing approaches is difficult when each uses a different repo, framework, and deployment model.

### Secondary users

- **Need:** Clean, well-structured code and documentation that explains the "why" alongside the "how".
- **Need:** Architecture diagrams and clear README files for each sub-project.
- **Pain point:** Most secure ML repos are research code — hard to read, poorly documented, and not structured for learning.

## Competitive Landscape

### Existing resources

| Resource | Strengths | Weaknesses |
|---|---|---|
| **Flower framework tutorials** | Good federated learning examples, multi-framework support | Local-only demos, no cloud deployment |
| **Concrete-ML documentation** | Thorough API docs, example notebooks | No AWS deployment patterns, limited real-world dataset examples |
| **AWS Nitro Enclaves examples** | Official AWS samples exist | Sparse, focused on KMS use cases rather than ML/LLM inference |
| **PySyft tutorials** | Privacy-preserving ML focus | Complex setup, heavy abstraction, not AWS-native |
| **Academic papers / blog posts** | Strong theoretical grounding | No runnable code, or code is throwaway quality |

### Opportunity

No single repository provides deployable, AWS-native reference implementations across multiple secure ML paradigms with consistent structure, IaC, and documentation. This project fills that gap.

## Success Criteria

1. **Deployable:** Each sub-project can be deployed to AWS using `cdk deploy` (plus any necessary Python setup) and produces a working, testable system.
2. **Functional:** Each sub-project demonstrates its core privacy-preserving technique end-to-end:
   - Federated learning: multiple simulated clients train a model on MNIST by exchanging gradients, producing a usable classifier.
   - FHE: a decision tree fraud detection model trains and/or infers on encrypted financial data using Concrete-ML.
   - Nitro Enclave: a user sends encrypted input to an enclave, which constructs a prompt and calls Bedrock (Claude), returning a response — functioning as a secure confidential financial advice chatbot with a minimal web UI.
3. **Cost-managed:** The Nitro Enclave infrastructure automatically tears down after 30 minutes of inactivity, enforced via CI/CD automation.
4. **Readable:** A developer unfamiliar with the project can understand the purpose, architecture, and execution flow of each sub-project by reading the code and documentation.

## Assumptions and Constraints

### Assumptions

- A single AWS account with sufficient permissions is available for deployment.
- The AWS account has access to Bedrock Claude models in the target region.
- Nitro Enclave-capable instance types are available in the target region.
- Public datasets (MNIST, a public fraud detection dataset such as the Kaggle credit card fraud dataset) are sufficient for demonstration purposes.
- Concrete-ML's supported model types (decision trees, logistic regression) are adequate for the FHE sub-project; deep learning under FHE is out of scope.

### Constraints

- **Language:** Python for application code; TypeScript for CDK infrastructure.
- **Cloud:** AWS only — no multi-cloud.
- **Cost:** Nitro Enclave instances must auto-terminate after 30 minutes of inactivity.
- **Repo structure:** Monorepo with three sub-projects (`federated/`, `fhe/`, `enclave/`).
- **Scope:** Each sub-project is a focused demonstration, not a production system.

## Resolved Decisions

1. **Federated learning framework:** Flower — mature, widely adopted, good simulation support.
2. **FHE dataset:** Kaggle credit card fraud dataset. The dataset must be downloaded manually by the user (Kaggle requires authentication); instructions will be provided.
3. **Nitro Enclave client interface:** Minimal web UI themed as a confidential financial advice chatbot.
4. **CI/CD platform:** GitHub Actions.
5. **Bedrock model:** Claude (via Bedrock).

## Open Questions

None — all questions resolved. Ready for handoff to PM.
