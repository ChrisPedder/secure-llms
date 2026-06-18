# Documentation and Developer Experience

**Epic:** Documentation and Developer Experience

**Refs:** DX-1, DX-2, DX-3

## User Story

As a public repository visitor, I want clear documentation with architecture diagrams and setup instructions for each sub-project so that I can understand the purpose, architecture, and execution flow without needing to deploy anything.

## Acceptance Criteria

- [x] Root `README.md` includes: project overview, table of the three approaches with one-sentence descriptions, links to sub-project READMEs, prerequisites, infra table, clean up, CI/CD
- [x] `federated/README.md` includes: overview, ASCII architecture diagram, prerequisites, local setup + run instructions, AWS deploy + run instructions, expected output
- [x] `fhe/README.md` includes: overview, ASCII architecture diagram, prerequisites, Kaggle dataset download instructions, local setup + run instructions, AWS deploy + run instructions, actual expected output from run
- [x] `enclave/README.md` includes: overview, ASCII diagram showing encryption boundaries and trust zones, prerequisites (including Bedrock model access), AWS deploy instructions, usage instructions, auto-teardown explanation, cost warning
- [x] Each architecture diagram clearly shows: what data is encrypted, where encryption/decryption occurs, what crosses trust boundaries
- [x] Each README includes a "Clean Up" section with `cdk destroy` instructions

## Technical Notes

- Architecture diagrams can be ASCII art in the README (consistent with `docs/architecture.md`) or Mermaid diagrams (rendered by GitHub)
- The enclave README should emphasise the cost implications of `c5.xlarge` and the auto-teardown mechanism
- Include the Bedrock model access request steps (AWS console → Bedrock → Model access → Request access for Claude)
- Keep instructions concrete: exact commands, expected output snippets

## Implementation Subtasks

- [x] Write root `README.md`
- [x] Write `federated/README.md` with diagram and instructions
- [x] Write `fhe/README.md` with diagram, Kaggle instructions, and expected output
- [x] Write `enclave/README.md` with diagram, cost warning, and teardown explanation
- [x] Verify all linting and tests pass across entire repo

## Status

Todo | In Progress | In Review | **Done**
