# FHE Fraud Detection Core ML

**Epic:** FHE Fraud Detection (Concrete-ML)

**Refs:** FHE-1, FHE-2, FHE-3, FHE-4, FHE-6, FHE-7

## User Story

As a practitioner, I want to train a fraud detection model on both plaintext and FHE-encrypted data locally so that I can compare accuracy and performance to understand the trade-offs of fully homomorphic encryption.

## Acceptance Criteria

- [x] `fhe/src/preprocess.py` loads `creditcard.csv`, undersamples the majority class, and splits into train/test sets
- [x] `fhe/src/baseline.py` trains a scikit-learn `DecisionTreeClassifier` and reports accuracy, precision, recall, and F1
- [x] `fhe/src/encrypted.py` trains a Concrete-ML `DecisionTreeClassifier`, compiles it to an FHE circuit, generates keys, and infers on encrypted test data
- [x] `fhe/src/compare.py` runs both paths and prints a side-by-side comparison table (metrics + wall-clock time)
- [x] `fhe/src/run.py` accepts `--local --data-path PATH` and orchestrates the full pipeline
- [x] Running `python run.py --local --data-path ./data/creditcard.csv` completes and prints the comparison table
- [x] FHE inference on a single sample completes within 60 seconds (NFR-6) — measured ~1.86s/sample
- [x] README includes step-by-step instructions for downloading `creditcard.csv` from Kaggle
- [x] A validation check at startup prints a clear error if `creditcard.csv` is not found
- [x] Unit tests exist for preprocessing logic (5 tests pass)

## Technical Notes

- See architecture.md: FHE Fraud Detection Data Flow, Component Breakdown
- Kaggle credit card fraud dataset: 284,807 transactions, 492 frauds (0.17%), 30 features (V1-V28 + Time + Amount) + Class
- Undersampling: take all fraud samples + equal random sample of non-fraud for balanced training
- Concrete-ML's `DecisionTreeClassifier` mirrors sklearn's API: `fit()`, `compile()`, `predict()` (on encrypted data)
- FHE compilation step may take a while — log progress
- Pin Concrete-ML version in `pyproject.toml`

## Implementation Subtasks

- [x] Implement `preprocess.py` with undersampling and train/test split
- [x] Implement `baseline.py` with sklearn decision tree
- [x] Implement `encrypted.py` with Concrete-ML decision tree
- [x] Implement `compare.py` with side-by-side output
- [x] Implement `run.py` CLI entry point with dataset validation
- [x] Add Kaggle download instructions to README
- [x] Write tests for preprocessing
- [x] Run end-to-end locally and verify output

## Status

Todo | In Progress | In Review | **Done**
