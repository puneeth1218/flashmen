# Machine Learning Module Context & Implementation Status

> **Module**: `ml/`  
> **Status**: Milestone M2 (Ingestion) Stabilized · Milestone M3 (Feature Engineering) Implemented & Verified · 12/12 Unit Tests Passing  
> **Core Stack**: scikit-learn · pandas · numpy · SHAP · pytest  

---

## 1. Module Overview & Role
The `ml/` module provides unsupervised anomaly detection, feature engineering, and explainable triage for the **Bitcoin Traffic Monitor (Flashmen)** platform. It processes ingested transaction and network metadata to identify suspicious peer behavior, peel chains, CoinJoin mixers, and anomalous traffic bursts without requiring labelled training datasets.

---

## 2. Directory Structure & File Contents

```
ml/
├── __init__.py                   # Module exports: extract_wallet_features, extract_features, etc.
├── dataset_gen.py                # CLI tool to generate synthetic 14-column datasets with deterministic seeds, anomalies (peel-chain, mixers), and ground truth (`pattern_type`).
├── explainer.py                  # ShapExplainer wrapper for local feature attribution triage
├── feature_engineering.py        # [M3] Pipeline transforming raw transactions into wallet & IP feature matrices
├── model.py                      # IsolationForestAnomalyDetector wrapper with 0–100 risk score calibration
└── tests/                        # Unit testing suite
    ├── __init__.py               # Test package initialization
    ├── test_feature_engineering.py # [M3] Validates wallet metrics, volume math, ratios, shapes, and scaling
    ├── test_features.py          # Validates legacy dual-feature schema and empty DataFrame handling
    ├── test_ingestion.py         # [M2] Validates JSON/CSV parsing, stringified lists, UTC, and GeoIP fallback
    └── test_model.py             # Validates model training, prediction, score bounds, and SHAP dict format
```

---

## 3. What Has Been Implemented By This Point

### 3.1 Unsupervised Anomaly Detection (`model.py`)
- **`IsolationForestAnomalyDetector` Class**:
  - Configured with `contamination=0.05` (5% expected anomaly rate) and 100 decision trees (`n_estimators=100`).
  - Implements standard scikit-learn lifecycle methods:
    - `fit(X)`: Fits the ensemble on numerical feature matrices.
    - `predict(X)`: Returns binary anomaly labels (`-1` for anomaly, `+1` for normal).
    - `score_samples(X)`: Computes raw decision function offset and normalizes values to an intuitive **0.0 to 100.0 risk score scale** (higher score = more anomalous).
  - Robust exception handling when scoring before fitting (`ValueError`).

### 3.2 Feature Attribution & Explainability (`explainer.py`)
- **`ShapExplainer` Class**:
  - Implements `explain_instance(feature_row: pd.Series) -> Dict[str, float]`.
  - Generates normalized feature attribution percentages (summing to ~1.0) to highlight which metrics drove the anomaly classification.
  - Serves as the interface contract for TreeExplainer integration.

### 3.3 Synthetic Data Generator (`dataset_gen.py`)
- **`generate_synthetic_dataset(num_records, seed)`**:
  - Generates realistic test records with Faker IPv4 addresses, random standard Bitcoin P2P ports (8333, 8332, 18333, non-standard ephemeral ports), valid ASNs, ISO-2 country codes, and 64-character hex transaction IDs.
  - Injects ~5% targeted anomalous behavior (peel-chains, mixers, and IP spoofing) to test detection models, alongside ~95% normal traffic.
  - Outputs a deterministic `pattern_type` column to serve as the ground truth label for anomaly detection evaluation.
  - Supports direct CLI execution with reproducibility: `python ml/dataset_gen.py --output data/synthetic/sample_traffic.csv --rows 500 --seed 42`.

### 3.4 Production Feature Engineering Pipeline (`feature_engineering.py`) — Milestone M3
- **`extract_wallet_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]`**:
  - **List Unnesting & Alignment**: Maps `input_addresses` with `input_amounts` and `output_addresses` with `output_amounts`. Safely handles stringified JSON lists, comma-separated strings, and mismatched array lengths.
  - **Aggregated Wallet Metrics**:
    - `tx_count`: Total unique transactions involving the wallet.
    - `total_volume_in`: Total incoming BTC/satoshis (from output amounts directed to wallet).
    - `total_volume_out`: Total outgoing BTC/satoshis (from input amounts spent by wallet).
    - `fan_out_ratio`: Ratio of unique outputs to unique inputs ($N_{out} / N_{in}$) across transactions involving the wallet (detects peel chains).
    - `fan_in_ratio`: Ratio of unique inputs to unique outputs ($N_{in} / N_{out}$) across transactions involving the wallet (detects mixers/consolidation).
    - `unique_ips_used`: Distinct count of observed `src_ip` peers associated with the wallet.
  - **Data Sanitization & Scaling**:
    - Replaces `NaN`, `+inf`, `-inf`, and zero division results with `0.0`.
    - Normalizes the raw numerical feature matrix using `sklearn.preprocessing.StandardScaler`.
    - Gracefully handles empty and single-wallet DataFrames.
- **`extract_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]`**:
  - Preserved dual IP and wallet extraction interface to maintain backward compatibility with `backend/services/scoring.py`, `graph/`, and existing test suites.

### 3.5 Test Suite & Quality Assurance (`tests/`)
All 12 unit tests across the ML suite pass cleanly with zero warnings:
```bash
$ python -m pytest -v ml/tests/
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-8.4.2, pluggy-1.5.0
rootdir: C:\Users\Praneeth Tadi\Documents\_SIH_bitcoin_traffic_monitor\flashmen
plugins: anyio-4.10.0
collected 12 items

ml/tests/test_feature_engineering.py::test_wallet_volume_aggregation PASSED [  8%]
ml/tests/test_feature_engineering.py::test_fan_in_and_fan_out_ratios PASSED [ 16%]
ml/tests/test_feature_engineering.py::test_scaled_matrix_dimensions_and_no_nan_inf PASSED [ 25%]
ml/tests/test_feature_engineering.py::test_unique_ips_used PASSED        [ 33%]
ml/tests/test_feature_engineering.py::test_empty_and_single_wallet_dataframe PASSED [ 41%]
ml/tests/test_features.py::test_extract_features_schema PASSED           [ 50%]
ml/tests/test_features.py::test_extract_features_empty_dataframe PASSED  [ 58%]
ml/tests/test_ingestion.py::test_process_raw_file_json PASSED            [ 66%]
ml/tests/test_ingestion.py::test_process_raw_file_csv PASSED             [ 75%]
ml/tests/test_ingestion.py::test_invalid_data_dropping PASSED            [ 83%]
ml/tests/test_model.py::test_isolation_forest_fit_predict PASSED         [ 91%]
ml/tests/test_model.py::test_shap_explainer PASSED                       [100%]

============================= 12 passed in 1.38s ==============================
```

---

## 4. Immediate Next Steps (Milestone M4)
1. **Model Pipeline Integration**:
   - Fit `IsolationForestAnomalyDetector` on the scaled wallet matrix produced by `extract_wallet_features()`.
   - Wire real inference into `backend/services/scoring.py:score_entities()`.
2. **Real TreeExplainer Integration**:
   - Replace Dirichlet synthetic attributions in `explainer.py` with true TreeExplainer/KernelExplainer feature attributions computed on the fitted Isolation Forest model.
3. **Graph Heuristic Fusion**:
   - Combine topological peel-chain alerts from `graph/heuristics.py` with ML anomaly scores for multi-layered forensic confidence scores.
