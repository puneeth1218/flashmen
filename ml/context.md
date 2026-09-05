# Machine Learning Module Context & Implementation Status

> **Module**: `ml/`  
> **Status**: Milestone M2 (Ingestion) Stabilized · Milestone M3 (Feature Engineering, Isolation Forest & SHAP TreeExplainer) Fully Completed & Verified · 21/21 Unit Tests Passing  
> **Core Stack**: scikit-learn · pandas · numpy · SHAP · pytest  

---

## 1. Module Overview & Role
The `ml/` module provides unsupervised anomaly detection, feature engineering, and explainable triage for the **Bitcoin Traffic Monitor (Flashmen)** platform. It processes ingested transaction and network metadata to identify suspicious peer behavior, peel chains, CoinJoin mixers, and anomalous traffic bursts without requiring labelled training datasets.

---

## 2. Directory Structure & File Contents

```
ml/
├── __init__.py                   # Module exports: extract_wallet_features, extract_features, IsolationForestAnomalyDetector, ShapExplainer
├── dataset_gen.py                # CLI tool to generate synthetic 14-column datasets with deterministic seeds, anomalies (peel-chain, mixers), and ground truth
├── explainer.py                  # Real SHAP TreeExplainer wrapper with normalized 100% feature attributions
├── feature_engineering.py        # [M3] Pipeline transforming raw transactions into wallet & IP feature matrices
├── model.py                      # [M3] IsolationForestAnomalyDetector with 0–100 risk score calibration & signal breakdown
└── tests/                        # Automated unit testing suite (21 tests)
    ├── __init__.py               # Test package initialization
    ├── test_feature_engineering.py # [M3] Validates wallet metrics, volume math, ratios, shapes, and scaling (5 tests)
    ├── test_features.py          # Validates legacy dual-feature schema and empty DataFrame handling (2 tests)
    ├── test_ingestion.py         # [M2] Validates JSON/CSV parsing, stringified lists, UTC, and GeoIP fallback (3 tests)
    └── test_model.py             # [M3] Validates model fitting, score calibration, outlier discrimination & SHAP TreeExplainer (11 tests)
```

---

## 3. What Has Been Implemented

### 3.1 Unsupervised Anomaly Detection & Risk Scoring Engine (`model.py`) — Milestone M3
- **`IsolationForestAnomalyDetector` Class**:
  - Configured with `contamination=0.02` (2% expected anomaly rate), `random_state=42`, and 100 decision trees (`n_estimators=100`).
  - **Dual Input Compatibility**: Accepts either pandas DataFrames or normalized 2D NumPy arrays from `extract_wallet_features()`.
  - Implements robust lifecycle methods:
    - `fit(X, feature_names=None)`: Fits the ensemble and records baseline feature distributions (mean, std) and training score bounds.
    - `predict(X)`: Returns binary anomaly labels (`-1` for anomaly, `+1` for normal inliers).
    - `score_samples(X)`: Calibrates raw IsolationForest anomaly scores to an intuitive **0.0 to 100.0 risk score scale** (higher score = more anomalous, strictly bounded in `[0.0, 100.0]`).
    - `explain_instance(feature_row)`: Computes normalized Z-score feature attribution weights summing to 1.0.
    - `get_signal_breakdown(feature_row, top_n)`: Returns descending-ordered feature contributions to highlight which specific metrics (e.g. `fan_out_ratio`, `unique_ips_used`, `total_volume_out`) triggered the anomaly.
    - `get_feature_attributions(X)`: Batch signal breakdown computation across all instances.
  - Robust exception handling when calling `predict`, `score_samples`, or `explain_instance` before `fit` (`ValueError`).

### 3.2 Real SHAP TreeExplainer Engine (`explainer.py`) — Milestone M3
- **`ShapExplainer` Class**:
  - Wraps `shap.TreeExplainer` over scikit-learn's `IsolationForest` estimators.
  - Computes local tree-path Shapley values explaining why specific wallet vectors deviate from the expected ensemble decision surface.
  - Normalizes absolute weights so $\sum w_j = 1.0$ (100%) per wallet.
  - Mapped directly to human-readable investigative tags:
    - `fan_out_ratio`: `"High Fan-Out (Peel Chain Pattern)"`
    - `unique_ips_used`: `"Rapid Multi-IP Broadcast"`
    - `total_volume_out`: `"Unusual Volume Surge (Outflow)"`
    - `total_volume_in`: `"Unusual Volume Surge (Inflow)"`
    - `fan_in_ratio`: `"High Fan-In (Mixer / Consolidation Pattern)"`
    - `tx_count`: `"Abnormal Transaction Velocity"`
  - Safely falls back to Z-score attribution if uniform matrices or uninitialized states are encountered.

### 3.3 Synthetic Data Generator (`dataset_gen.py`)
- **`generate_synthetic_dataset(num_records, seed)`**:
  - Generates realistic test records with Faker IPv4 addresses, random standard Bitcoin P2P ports (8333, 8332, 18333, non-standard ephemeral ports), valid ASNs, ISO-2 country codes, and 64-character hex transaction IDs.
  - Injects ~5% targeted anomalous behavior (peel-chains, mixers, and IP spoofing) to test detection models, alongside ~95% normal traffic.
  - Outputs a deterministic `pattern_type` column to serve as ground-truth labels for evaluation.

### 3.4 Production Feature Engineering Pipeline (`feature_engineering.py`) — Milestone M3
- **`extract_wallet_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]`**:
  - **List Unnesting & Alignment**: Maps `input_addresses` with `input_amounts` and `output_addresses` with `output_amounts`.
  - **6 Aggregated Wallet Metrics**:
    1. `tx_count`: Total unique transactions involving the wallet.
    2. `total_volume_in`: Total incoming BTC/satoshis.
    3. `total_volume_out`: Total outgoing BTC/satoshis.
    4. `fan_out_ratio`: Ratio of unique outputs to inputs ($N_{out} / N_{in}$, detects peel chains).
    5. `fan_in_ratio`: Ratio of unique inputs to outputs ($N_{in} / N_{out}$, detects mixers/consolidation).
    6. `unique_ips_used`: Distinct count of observed `src_ip` peers associated with the wallet.
  - **Data Sanitization & Scaling**: Replaces `NaN`, `+inf`, `-inf` with `0.0` and normalizes the matrix using `sklearn.preprocessing.StandardScaler`.
- **`extract_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]`**: Preserved dual IP/wallet interface for backward compatibility.

---

## 4. Setup & Running Instructions

> [!IMPORTANT]
> Always execute ML commands from the **repository root (`flashmen/`)**.

### Generate Synthetic Test Data:
```bash
python -m ml.dataset_gen --output data/synthetic/sample_traffic.csv --rows 500
```

### Run Automated Pytest Suite (21 Tests):
```bash
pytest ml/tests/
```

### Run Specific Test Modules:
```bash
# Feature engineering tests
pytest ml/tests/test_feature_engineering.py

# Model training & SHAP TreeExplainer tests
pytest ml/tests/test_model.py

# Ingestion pipeline tests
pytest ml/tests/test_ingestion.py
```

