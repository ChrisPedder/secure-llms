# Repository Foundation

**Epic:** Repository Foundation

**Refs:** RF-1, RF-2, RF-3, RF-4

## User Story

As a developer, I want a well-structured monorepo with shared infrastructure, per-project dependency management, and CI so that each sub-project can be developed and deployed independently.

## Acceptance Criteria

- [x] Root directory contains `federated/`, `fhe/`, `enclave/`, `infra/`, `docs/`, and `.github/` directories
- [x] Each sub-project has `README.md`, `src/`, `tests/`, `infra/`, `pyproject.toml`, and `Dockerfile`
- [x] `fhe/data/` exists with `.gitkeep` and is `.gitignore`d (except `.gitkeep`)
- [x] Shared CDK app in `infra/` provisions a VPC (2 AZs, public + private subnets, NAT gateway) with CloudFormation exports (`SecureLlmsVpcId`, `SecureLlmsPublicSubnetIds`, `SecureLlmsPrivateSubnetIds`)
- [x] Each sub-project has a `pyproject.toml` with its dependencies and a `uv.lock`
- [x] Root `pyproject.toml` contains ruff configuration only (no dependencies)
- [x] `.gitignore` covers `*.env`, `credentials*`, `*.pem`, `*.key`, `data/creditcard.csv`, Python artifacts, `node_modules/`, `cdk.out/`
- [x] GitHub Actions `ci.yml` runs lint (ruff + eslint) and test (pytest) jobs for each sub-project independently on push to `main`
- [x] All CDK projects have `package.json`, `tsconfig.json`, and eslint configuration
- [x] All resources tagged with `Project: secure-llms`

## Technical Notes

- See architecture.md: File Structure Conventions, ADR-004, ADR-005, Coding Standards
- CDK apps follow `bin/app.ts` + `lib/*-stack.ts` pattern
- Sub-project CDK stacks import shared VPC via `Fn.importValue`
- CI should use `uv` for Python dependency installation
- Each sub-project's CI job should be independent (use `paths` filter or matrix strategy)

## Implementation Subtasks

- [x] Create directory structure for all sub-projects
- [x] Write root `pyproject.toml` with ruff config
- [x] Write `pyproject.toml` for each sub-project with placeholder dependencies
- [x] Write shared CDK stack (`infra/lib/shared-stack.ts`)
- [x] Write placeholder CDK stacks for each sub-project
- [x] Write `.gitignore`
- [x] Write `ci.yml` GitHub Actions workflow
- [x] Write `enclave-teardown.yml` placeholder workflow
- [x] Verify `uv sync` works in each sub-project

## Status

Todo | In Progress | **In Review** | Done
