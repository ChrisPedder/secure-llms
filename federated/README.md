# Federated Learning with Flower on MNIST

Privacy-preserving ML via federated averaging -- multiple simulated clients train a CNN on local MNIST partitions, exchanging only model weight updates with a central server. No raw training data ever leaves the client.

## Architecture

```
                        ┌──────────────────┐
                        │   Flower Server   │
                        │   (FedAvg)        │
                        │                   │
                        │  Global model     │
                        │  weights          │
                        └──┬─────┬──────┬──┘
               gradients   │     │      │   gradients
              ┌────────────┘     │      └────────────┐
              ▼                  ▼                    ▼
      ┌──────────────┐  ┌──────────────┐     ┌──────────────┐
      │   Client 1   │  │   Client 2   │     │   Client N   │
      │              │  │              │ ... │              │
      │  MNIST       │  │  MNIST       │     │  MNIST       │
      │  partition 1 │  │  partition 2 │     │  partition N │
      └──────────────┘  └──────────────┘     └──────────────┘

      Only weight updates cross the boundary -- raw images stay local.
```

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Local Setup and Run

```bash
cd federated
uv sync --dev
uv run python -m src.run --local --rounds 5 --clients 3
```

MNIST is downloaded automatically on first run.

### Expected Output

```
[ROUND 1] Global accuracy: 0.8512
[ROUND 2] Global accuracy: 0.9234
...
[ROUND 5] Global accuracy: 0.9872
```

Expect >90% accuracy after 5 rounds with 3 clients.

## AWS Deployment

### Deploy

```bash
# Deploy shared VPC first (if not already done)
cd infra && npx cdk deploy && cd ..

# Deploy federated stack
cd federated/infra
npm install
npx cdk deploy
```

### Run on Fargate

```bash
cd federated
./scripts/run-task.sh
```

The script fetches stack outputs, starts a Fargate task, and streams CloudWatch logs.

## Tests

```bash
uv run pytest tests/ -v
```

## Clean Up

```bash
cd federated/infra && npx cdk destroy
```
