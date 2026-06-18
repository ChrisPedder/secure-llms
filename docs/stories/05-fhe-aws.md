# FHE Fraud Detection AWS Deployment

**Epic:** FHE Fraud Detection (Concrete-ML)

**Refs:** FHE-5

## User Story

As a practitioner, I want to deploy the FHE fraud detection pipeline to AWS via CDK so that I can run the training and inference on cloud compute.

## Acceptance Criteria

- [x] `fhe/Dockerfile` packages the Python application for Fargate (with boto3 for S3 access)
- [x] `fhe/infra/lib/fhe-stack.ts` defines an ECS Fargate task (4 vCPU, 8 GB memory) and an S3 bucket for data
- [x] The stack imports the shared VPC via tag-based lookup
- [x] CDK uses `ContainerImage.fromAsset` for automatic ECR image build and push
- [x] The Fargate task reads `creditcard.csv` from S3 (run-task.sh uploads it first)
- [x] Results (comparison table) are written to CloudWatch logs
- [ ] `cdk deploy` provisions all resources; `cdk destroy` cleanly removes them — requires live AWS
- [x] All resources tagged with `Project: secure-llms` and `SubProject: fhe`

## Technical Notes

- See architecture.md: ADR-003, ADR-004
- The Fargate task runs `python run.py --data-path s3://bucket/creditcard.csv`
- The `run.py` script should support S3 paths (download to local temp before processing) or accept a local path
- 4 vCPU / 8 GB should be sufficient for a decision tree on the credit card dataset under FHE
- Task auto-stops when the pipeline completes

## Implementation Subtasks

- [x] Write `fhe/Dockerfile`
- [x] Implement `fhe-stack.ts` with Fargate task + S3 bucket
- [x] Add S3 download support to `run.py` (detect `s3://` prefix)
- [x] Write `scripts/run-task.sh` (uploads data + triggers task + streams logs)
- [ ] Test `cdk deploy` → upload data → run task → verify results → `cdk destroy` (requires live AWS)

## Status

Todo | In Progress | In Review | **Done**
