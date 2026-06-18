# Nitro Enclave AWS Deployment and Auto-Teardown

**Epic:** Nitro Enclave Secure Chatbot (Bedrock Claude)

**Refs:** NE-5, NE-6, NE-7

## User Story

As a practitioner, I want to deploy the enclave chatbot to AWS with a single `cdk deploy` command and have it automatically shut down after 30 minutes of inactivity so that I can test the system without worrying about cost overruns.

## Acceptance Criteria

- [x] `enclave/infra/lib/enclave-stack.ts` provisions: EC2 `c5.xlarge` (enclave-enabled), security groups (HTTPS inbound), KMS RSA asymmetric key, CloudWatch alarm, SNS topic, Lambda function
- [x] The EC2 instance has `EnclaveOptions: Enabled` and runs Amazon Linux 2023
- [x] User data script installs dependencies, starts `vsock-proxy` for KMS and Bedrock, builds the EIF, and starts the enclave + parent server
- [x] KMS key grants Decrypt and GetPublicKey to instance role (PCR attestation gating noted for production hardening)
- [x] `kms:GetPublicKey` is allowed for the parent instance role (no attestation required)
- [x] The parent publishes a custom CloudWatch metric (`LastRequestTimestamp`) on each `/chat` request (gated by PUBLISH_METRICS env var)
- [x] A CloudWatch alarm triggers when no data points are received for 30 minutes (INSUFFICIENT_DATA → ALARM)
- [x] The alarm sends to an SNS topic that invokes a Lambda function
- [x] The Lambda function stops the EC2 instance
- [x] `enclave-teardown.yml` GitHub Actions workflow runs every 6 hours as a fallback check
- [x] `cdk deploy` outputs the instance public IP and KMS key ID
- [ ] `cdk destroy` cleanly removes all resources — requires live AWS
- [x] All resources tagged with `Project: secure-llms` and `SubProject: enclave`

## Technical Notes

- See architecture.md: ADR-002 (KMS RSA key), ADR-004, Technical Risks (EIF build, auto-teardown)
- EIF must be built on the EC2 instance itself (nitro-cli requires Amazon Linux on Nitro hardware)
- The user data script is the main orchestration point: install nitro-cli, docker, python, build EIF, start enclave, start Flask
- PCR values are determined after the first EIF build; update the KMS key policy with actual values
- For the MVP, PCR values can be set to allow any enclave on the instance (PCR0 only) and tightened later
- vsock-proxy commands: `vsock-proxy 8443 kms.{region}.amazonaws.com 443` and `vsock-proxy 8444 bedrock-runtime.{region}.amazonaws.com 443`
- Budget alert: consider adding an AWS Budgets alarm as a safety net

## Implementation Subtasks

- [x] Implement `enclave-stack.ts` with EC2 instance, security groups, instance profile
- [x] Add KMS RSA asymmetric key
- [x] Write EC2 user data script (install deps, build EIF, start services)
- [x] Implement CloudWatch custom metric publishing in parent `server.py`
- [x] Add CloudWatch alarm + SNS + Lambda for auto-teardown
- [x] Lambda teardown function already implemented in story 01
- [x] Write `enclave-teardown.yml` GitHub Actions fallback workflow
- [ ] Test full deployment lifecycle — requires live AWS

## Status

Todo | In Progress | In Review | **Done**
