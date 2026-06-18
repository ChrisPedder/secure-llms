# Federated Learning Core ML

**Epic:** Federated Learning (Flower + MNIST)

**Refs:** FL-1, FL-2, FL-3, FL-4, FL-6

## User Story

As a practitioner, I want to run a complete federated learning training loop locally using Flower with simulated clients on MNIST so that I can understand how federated averaging works without needing cloud infrastructure.

## Acceptance Criteria

- [x] `federated/src/model.py` defines a CNN (2 conv layers + 2 FC layers) suitable for MNIST
- [x] `federated/src/data.py` auto-downloads MNIST (via torchvision) and partitions it into N non-overlapping shards
- [x] `federated/src/client.py` implements a Flower `NumPyClient` that trains the CNN on a local MNIST partition
- [x] `federated/src/server.py` configures a Flower server with FedAvg strategy
- [x] `federated/src/run.py` accepts `--local --rounds N --clients N` and runs the full simulation
- [x] Running `python run.py --local --rounds 5 --clients 3` trains successfully and prints per-round and final accuracy
- [x] Final global model achieves ≥90% accuracy on the MNIST test set (achieved 98.72%)
- [x] No raw MNIST data leaves the client — only model weight updates are exchanged
- [x] Unit tests exist for model forward pass and data partitioning (5 tests)

## Technical Notes

- See architecture.md: Federated Learning Data Flow, Component Breakdown
- Use `flwr.simulation.start_simulation()` for local mode (ADR-001)
- PyTorch CNN: Conv2d(1,32,3) → Conv2d(32,64,3) → FC(9216,128) → FC(128,10) is a reasonable starting point
- Partition MNIST by assigning each sample to a client based on index modulo N (simple) or by digit groups for non-IID exploration
- Print accuracy per round to stdout for observability

## Implementation Subtasks

- [x] Implement CNN in `model.py`
- [x] Implement MNIST download + partitioning in `data.py`
- [x] Implement Flower NumPyClient in `client.py`
- [x] Implement Flower server with FedAvg in `server.py`
- [x] Implement CLI entry point in `run.py` with `--local` mode
- [x] Write tests for model and data modules
- [x] Run end-to-end locally and verify ≥90% accuracy

## Status

Todo | In Progress | In Review | **Done**
