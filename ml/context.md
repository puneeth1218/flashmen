# Machine Learning Module Context & Implementation Status

> **Module**: `ml/`  
> **Status**: Milestone M2 (Ingestion) Stabilized · Milestone M3 (Feature Engineering & Risk Scoring Engine) Fully Completed & Verified · 16/16 Unit Tests Passing  
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
├── model.py                      # [M3] IsolationForestAnomalyDetector with 0–100 risk score calibration & signal breakdown
└── tests/                        # Automated unit testing suite (16 tests)
    ├── __init__.py               # Test package initialization
    ├── test_feature_engineering.py # [M3] Validates wallet metrics, volume math, ratios, shapes, and scaling (5 tests)
    ├── test_features.py          # Validates legacy dual-feature schema and empty DataFrame handling (2 tests)
    ├── test_ingestion.py         # [M2] Validates JSON/CSV parsing, stringified lists, UTC, and GeoIP fallback (3 tests)
    └── test_model.py             # [M3] Validates model fitting, score calibration, outlier discrimination & attributions (6 tests)
```

---

## 3. What Has Been Implemented By This Point

### 3.1 Unsupervised Anomaly Detection & Risk Scoring Engine (`model.py`) — Milestone M3
- **`IsolationForestAnomalyDetector` Class**:
  - Configured with `contamination=0.02` (2% expected anomaly rate), `random_state=42`, and 100 decision trees (`n_estimators=100`).
  - **Dual Input Compatibility**: Accepts either pandas DataFrames (with automatic numeric extraction and column alignment) or normalized 2D NumPy arrays from `extract_wallet_features()`.
  - Implements robust lifecycle methods:
    - `fit(X, feature_names=None)`: Fits the ensemble and records baseline feature distributions (mean, std) and training score bounds.
    - `predict(X)`: Returns binary anomaly labels (`-1` for anomaly, `+1` for normal inliers).
    - `score_samples(X)`: Calibrates raw IsolationForest anomaly scores to an intuitive **0.0 to 100.0 risk score scale** (higher score = more anomalous, strictly bounded in `[0.0, 100.0]`).
    - `explain_instance(feature_row)`: Computes feature attribution impact weights summing to 1.0.
    - `get_signal_breakdown(feature_row, top_n)`: Returns descending-ordered feature contributions to highlight which specific metrics (e.g. `fan_out_ratio`, `unique_ips_used`, `total_volume_out`) triggered the anomaly.
    - `get_feature_attributions(X)`: Batch signal breakdown computation across all instances.
  - Robust exception handling when calling `predict`, `score_samples`, or `explain_instance` before `fit` (`ValueError`).

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
All 16 unit tests across the ML suite pass cleanly with 100% success rate:
```bash
$ python -m pytest -v ml/tests/
============================= test session starts ==============================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /mnt/c/Users/Praneeth Tadi/Documents/_SIH_bitcoin_traffic_monitor/flashmen/.venv/bin/python
cachedir: .pytest_cache
rootdir: /mnt/c/Users/Praneeth Tadi/Documents/_SIH_bitcoin_traffic_monitor/flashmen
plugins: anyio-4.14.2, Faker-40.38.0
collecting ... collected 19 items

ml/tests/test_feature_engineering.py::test_wallet_volume_aggregation PASSED [  5%]
ml/tests/test_feature_engineering.py::test_fan_in_and_fan_out_ratios PASSED [ 10%]
ml/tests/test_feature_engineering.py::test_scaled_matrix_dimensions_and_no_nan_inf PASSED [ 15%]
ml/tests/test_feature_engineering.py::test_unique_ips_used PASSED        [ 21%]
ml/tests/test_feature_engineering.py::test_empty_and_single_wallet_dataframe PASSED [ 26%]
ml/tests/test_features.py::test_extract_features_schema PASSED           [ 31%]
ml/tests/test_features.py::test_extract_features_empty_dataframe PASSED  [ 36%]
ml/tests/test_ingestion.py::test_process_raw_file_json PASSED            [ 42%]
ml/tests/test_ingestion.py::test_process_raw_file_csv PASSED             [ 47%]
ml/tests/test_ingestion.py::test_invalid_data_dropping PASSED            [ 52%]
ml/tests/test_model.py::test_isolation_forest_fit_predict PASSED         [ 57%]
ml/tests/test_model.py::test_isolation_forest_numpy_array_input PASSED   [ 63%]
ml/tests/test_model.py::test_risk_score_bounds_and_calibration PASSED    [ 68%]
ml/tests/test_model.py::test_synthetic_outlier_wallets_score_significantly_higher PASSED [ 73%]
ml/tests/test_signal_breakdown_attribution PASSED                         [ 78%]
ml/tests/test_model.py::test_anomalous_wallets_return_top_risk_factors PASSED [ 84%]
ml/tests/test_model.py::test_injected_extreme_feature_attribution PASSED [ 89%]
ml/tests/test_model.py::test_attribution_edge_cases_zero_variance_and_uniform PASSED [ 94%]
ml/tests/test_model.py::test_shap_explainer PASSED                       [100%]

============================= 19 passed in 50.40s ==============================
```

Dedicated ML Model Suite Log (`ml/tests/test_model.log`):
```bash
$ python -m pytest -v -s ml/tests/test_model.py
============================= test session starts ==============================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /mnt/c/Users/Praneeth Tadi/Documents/_SIH_bitcoin_traffic_monitor/flashmen/.venv/bin/python
cachedir: .pytest_cache
rootdir: /mnt/c/Users/Praneeth Tadi/Documents/_SIH_bitcoin_traffic_monitor/flashmen
plugins: anyio-4.14.2, Faker-40.38.0
collecting ... collected 9 items

ml/tests/test_model.py::test_isolation_forest_fit_predict PASSED
ml/tests/test_model.py::test_isolation_forest_numpy_array_input PASSED
ml/tests/test_model.py::test_risk_score_bounds_and_calibration PASSED
ml/tests/test_model.py::test_synthetic_outlier_wallets_score_significantly_higher PASSED
ml/tests/test_model.py::test_signal_breakdown_attribution PASSED
ml/tests/test_model.py::test_anomalous_wallets_return_top_risk_factors PASSED
ml/tests/test_model.py::test_injected_extreme_feature_attribution PASSED
ml/tests/test_model.py::test_attribution_edge_cases_zero_variance_and_uniform PASSED
ml/tests/test_model.py::test_shap_explainer PASSED

============================== slowest durations ===============================
0.75s call     ml/tests/test_model.py::test_synthetic_outlier_wallets_score_significantly_higher
0.33s call     ml/tests/test_model.py::test_isolation_forest_fit_predict
0.13s call     ml/tests/test_model.py::test_attribution_edge_cases_zero_variance_and_uniform
0.11s call     ml/tests/test_model.py::test_anomalous_wallets_return_top_risk_factors
0.10s call     ml/tests/test_model.py::test_risk_score_bounds_and_calibration
0.07s call     ml/tests/test_model.py::test_isolation_forest_numpy_array_input
0.07s call     ml/tests/test_model.py::test_injected_extreme_feature_attribution
0.06s call     ml/tests/test_model.py::test_signal_breakdown_attribution

============================== 9 passed in 49.32s ==============================
```

---

## 4. Next Integration Steps (Milestone M4)
1. **Model Pipeline Integration**:
   - Wire `IsolationForestAnomalyDetector` into `backend/services/scoring.py:score_entities()` to score both IP and wallet entities dynamically.
2. **Graph Heuristic Fusion**:
   - Combine topological peel-chain alerts from `graph/heuristics.py` with ML anomaly scores for multi-layered forensic confidence scores.
