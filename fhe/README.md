# FHE Fraud Detection with Concrete-ML

Privacy-preserving ML via fully homomorphic encryption -- a decision tree fraud detector trains on plaintext data, then compiles to an FHE circuit so inference runs entirely on encrypted inputs. Compared side-by-side against a plaintext sklearn baseline.

## Architecture

```
  ┌──────────────────────────────────────────────────────┐
  │                   FHE Pipeline                        │
  │                                                       │
  │  creditcard.csv ──► Preprocess (undersample, split)   │
  │                          │                            │
  │          ┌───────────────┴───────────────┐            │
  │          ▼                               ▼            │
  │   ┌─────────────┐               ┌──────────────┐     │
  │   │  Plaintext   │               │   FHE Path   │     │
  │   │  sklearn     │               │  Concrete-ML │     │
  │   │  Decision    │               │  Decision    │     │
  │   │  Tree        │               │  Tree        │     │
  │   │             │               │              │     │
  │   │  .fit()     │               │  .fit()      │     │
  │   │  .predict() │               │  .compile()  │     │
  │   │             │               │  keygen()    │     │
  │   │  Plaintext   │               │  .predict()  │     │
  │   │  inference   │               │  Encrypted   │     │
  │   └──────┬──────┘               │  inference   │     │
  │          │                       └──────┬──────┘     │
  │          └───────────┬──────────────────┘            │
  │                      ▼                                │
  │              Comparison Table                         │
  │         (accuracy, F1, wall-clock time)               │
  └──────────────────────────────────────────────────────┘

  The FHE path never sees plaintext at inference time --
  inputs are encrypted, computation runs on ciphertext.
```

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Dataset Setup

This project uses the [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) dataset.

1. Create a free Kaggle account at https://www.kaggle.com
2. Go to https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
3. Click "Download" to get `archive.zip`
4. Extract `creditcard.csv` from the archive
5. Place it at `fhe/data/creditcard.csv`

Alternatively, using the Kaggle CLI:

```bash
pip install kaggle
kaggle datasets download -d mlg-ulb/creditcardfraud -p data/ --unzip
```

## Local Setup and Run

```bash
cd fhe
uv sync --dev
uv run python -m src.run --local --data-path ./data/creditcard.csv
```

### Expected Output

```
Metric                    Plaintext          FHE       Diff
-----------------------------------------------------------
accuracy                     0.9155       0.8953    -0.0203
precision                    0.9424       0.8926    -0.0498
recall                       0.8851       0.8986    +0.0135
f1                           0.9129       0.8956    -0.0173
-----------------------------------------------------------
train_time_s                 0.0078       0.1430
compile_time_s                  N/A       1.0947
keygen_time_s                   N/A       0.9668
inference_time_s             0.0004     551.5342
-----------------------------------------------------------
Inference slowdown                               1492985.6x
-----------------------------------------------------------
```

FHE inference is ~1.86s per sample. The massive slowdown demonstrates the core FHE trade-off: strong privacy guarantees at significant computational cost.

## AWS Deployment

### Deploy

```bash
# Deploy shared VPC first (if not already done)
cd infra && npx cdk deploy && cd ..

# Deploy FHE stack
cd fhe/infra
npm install
npx cdk deploy
```

### Run on Fargate

```bash
cd fhe
./scripts/run-task.sh ./data/creditcard.csv
```

The script uploads the dataset to S3, starts a Fargate task (4 vCPU, 8 GB), and streams CloudWatch logs.

## Tests

```bash
uv run pytest tests/ -v
```

## Clean Up

```bash
cd fhe/infra && npx cdk destroy
```
