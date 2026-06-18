# Federated Learning AWS Deployment

**Epic:** Federated Learning (Flower + MNIST)

**Refs:** FL-5

## User Story

As a practitioner, I want to deploy the federated learning simulation to AWS via CDK so that I can run the training on cloud infrastructure and validate the IaC pattern.

## Acceptance Criteria

- [x] `federated/Dockerfile` packages the Python application for Fargate
- [x] `federated/infra/lib/federated-stack.ts` defines an ECS Fargate task that runs the Flower simulation
- [x] The stack imports the shared VPC via tag-based lookup (requires shared stack deployed first)
- [x] CDK uses `ContainerImage.fromAsset` for automatic ECR image build and push
- [x] `cdk deploy` provisions the ECS cluster, task definition, and CloudWatch log group
- [x] `federated/scripts/run-task.sh` triggers the Fargate task and streams CloudWatch logs
- [ ] Training results (accuracy) appear in CloudWatch logs — requires live AWS test
- [ ] `cdk destroy` cleanly removes all resources — requires live AWS test
- [x] All resources tagged with `Project: secure-llms` and `SubProject: federated`

## Technical Notes

- See architecture.md: ADR-001 (single Fargate task for simulation), ADR-003 (Fargate for batch), ADR-004 (per-project CDK)
- The Fargate task runs `python run.py --rounds 5 --clients 3` (no `--local` flag — same code, just containerised)
- Use a `RunTask` API call or a simple wrapper script to trigger the task
- Task should auto-stop when the simulation completes (Fargate charges per-second)
- NFR-5: training should complete within 30 minutes

## Implementation Subtasks

- [x] Write `federated/Dockerfile`
- [x] Implement `federated-stack.ts` with ECS Fargate task definition
- [x] Add CloudWatch log group configuration
- [x] Write `scripts/run-task.sh` trigger script
- [ ] Test `cdk deploy` → run task → verify logs → `cdk destroy` (requires live AWS)
- [x] Add `cdk.json` to all infra directories
- [x] Add `ts-node` dev dependency to all infra projects

## Status

Todo | In Progress | **In Review** | Done
