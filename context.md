# Project Context & Engineering Status: Bitcoin Traffic Monitor (Flashmen)

> **Repository**: `puneeth1218/flashmen`  
> **Role**: Senior Data & ML Engineer  
> **Status**: Milestone M2 (Ingestion) Stabilized · Milestone M3 (Feature Engineering, Risk Scoring, True SHAP TreeExplainer & Explainability) Fully Completed & Verified  
> **Environment Status**: Bound exclusively to Linux virtual environment `/home/praneeth_tadi/.flashmen_env` · Clean passing test suite (`/home/praneeth_tadi/.flashmen_env/bin/python -m pytest -v ml/tests/` -> 21/21 passed in WSL2, 100% pass rate)  

---

## 1. Project Overview & SIH Challenge (PS 26146 - NTRO)

### 1.1 Scope & Problem Statement
Under **Smart India Hackathon (SIH) Problem Statement 26146 (NTRO)**, this project delivers an **offline-capable, explainable anomaly detection and network traffic monitoring platform for Bitcoin (P2P network layer & blockchain transaction layer)**.

The objective is to enable cyber intelligence, forensic investigators, and network analysts to:
- Ingest asynchronous, multi-format Bitcoin traffic dumps (JSON/CSV) without live internet dependencies.
- Correlate network-layer peer observations (IP addresses, ports, ASNs, GeoIP, timestamps) with on-chain ledger actions (transaction IDs, input/output wallet addresses, satoshi/BTC flow).
- Isolate suspicious entities (e.g., rapid peel-chaining, CoinJoin mixers, sybil relay clusters, high-fan-out wash trading, and anomalous port/burst velocities) using unsupervised machine learning.
- Provide explainable triage (feature attributions, investigative reason tags) and interactive topological graph analysis (Cytoscape.js) to trace threat actors.

### 1.2 Core Operational Constraints
- **Air-Gapped & Offline Execution**: The entire pipeline operates in disconnected environments. GeoIP lookups utilize local MaxMind `.mmdb` databases (`data/geolite2/GeoLite2-City.mmdb`) with graceful fallback to `"UNKNOWN"`. All Python/Node dependencies are locally packaged.
- **Strict Non-Destructive Module Boundaries**: Parallel development requires isolating changes strictly to data ingestion (`backend/services/ingestion.py`) and machine learning (`ml/`), preserving existing contracts and avoiding touching `backend/routes/`, `frontend/`, or `graph/`.
- **Determinism & Performance**: Zero telemetry leaks, deterministic validation with Pydantic v2 schemas, vector-accelerated feature transforms in pandas/numpy, and lightweight ML scoring with low latency.

---

## 2. Active Architecture & Module Responsibilities

```
flashmen/
├── backend/                  # FastAPI Application & Services
│   ├── database.py           # SQLAlchemy engine & SQLite fallback
│   ├── main.py               # Application factory & router mounts
│   ├── routes/               # API endpoints (ingest, alerts, stats, graph, search)
│   └── services/
│       ├── ingestion.py      # [M2] Raw CSV/JSON ingestion, Pydantic v2 validation, GeoIP enrichment
│       └── scoring.py        # [M3->M1] AlertData generation & anomaly scoring contract
├── data/
│   ├── geolite2/             # MaxMind offline GeoIP binary (GeoLite2-City.mmdb)
│   └── synthetic/            # Synthetic sample files for testing
├── frontend/                 # React 18 SPA (Vite + TypeScript + Tailwind + Cytoscape.js)
├── graph/                    # NetworkX graph construction & heuristic pattern matchers
│   ├── builder.py            # Directed multigraph construction for Cytoscape.js
│   └── heuristics.py         # Peel-chain & CoinJoin/mixer topological detectors
└── ml/                       # Machine Learning Pipeline
    ├── __init__.py           # Package exports (extract_wallet_features, IsolationForestAnomalyDetector, ShapExplainer, etc.)
    ├── dataset_gen.py        # 14-column synthetic dataset generator
    ├── explainer.py          # [M3] True SHAP TreeExplainer wrapper (genuine local Shapley attributions, 100% normalized, forensic tags)
    ├── feature_engineering.py# [M3] List unnesting, wallet aggregations, scaling pipeline
    ├── model.py              # [M3] IsolationForestAnomalyDetector with 0-100 risk scoring & Z-score baseline explainability
    └── tests/                # Automated pytest suite (21 passing unit tests)
        ├── test_feature_engineering.py # M3 wallet metrics & scaling tests (5 tests)
        ├── test_features.py            # Legacy dual-feature compatibility tests (2 tests)
        ├── test_ingestion.py           # M2 JSON/CSV parsing & GeoIP fallback tests (3 tests)
        └── test_model.py               # M3 model training, risk scoring & SHAP explainability (11 tests)
```

---

## 3. Data Interface Contracts & Schema Specifications

### 3.1 M2 Ingestion Output Schema (`process_raw_file`)
Produced by `backend/services/ingestion.py:process_raw_file(filepath: str) -> pd.DataFrame` and consumed by M3 (`ml/feature_engineering.py`) and M4 (`ml/model.py`, `graph/builder.py`):

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `datetime64[ns, UTC]` | Standardized UTC timestamp of observed peer relay / block |
| `src_ip` | `string` | Source IPv4/IPv6 address of peer |
| `dst_ip` | `string` | Destination IPv4/IPv6 address of peer |
| `src_port` | `int` | Source TCP port |
| `dst_port` | `int` | Destination TCP port |
| `txid` | `string` | 64-character hexadecimal Bitcoin transaction ID |
| `input_addresses` | `List[str]` | List of input wallet addresses spending UTXOs |
| `output_addresses` | `List[str]` | List of output wallet addresses receiving funds |
| `input_amounts` | `List[float]` | Spent amounts per input address (BTC/Satoshis) |
| `output_amounts` | `List[float]` | Received amounts per output address (BTC/Satoshis) |
| `fee` | `float` | Miner fee (defaults to `0.0`) |
| `script_type` | `string` | Bitcoin script type (`p2pkh`, `p2wpkh`, `p2sh`, etc.) |
| `src_country` | `string` | ISO-2 country code from MaxMind or `"UNKNOWN"` |
| `dst_country` | `string` | ISO-2 country code from MaxMind or `"UNKNOWN"` |

### 3.2 M3 Feature Engineering Output Schema (`extract_wallet_features`)
Produced by `ml/feature_engineering.py:extract_wallet_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]`:

- **DataFrame Index**: `wallet_id` (string address)
- **Feature Columns**:
  1. `tx_count`: Total unique transactions involving the wallet as sender or receiver.
  2. `total_volume_in`: Sum of BTC received by the wallet across output amounts.
  3. `total_volume_out`: Sum of BTC disbursed by the wallet across input amounts.
  4. `fan_out_ratio`: Ratio of unique outputs to unique inputs ($N_{out} / N_{in}$) across transactions involving the wallet (elevated in peel chains).
  5. `fan_in_ratio`: Ratio of unique inputs to unique outputs ($N_{in} / N_{out}$) across transactions involving the wallet (elevated in mixers/consolidation).
  6. `unique_ips_used`: Distinct count of non-null `src_ip` values observed broadcasting transactions involving the wallet.
- **Scaled Matrix**: 2D `np.ndarray` of shape `(N, 6)` normalized using `sklearn.preprocessing.StandardScaler`, guaranteed free of NaN or infinite values.

### 3.3 M3 Model Training, Risk Scoring & Explainability Interface (`ml/model.py`)
Implemented by `ml/model.py:IsolationForestAnomalyDetector` and consumed by `backend/services/scoring.py` and Graph integration:

#### Forensic Factor Definitions & Investigative Tags
| Feature Column | Investigative Tag | Forensic Indicator |
| :--- | :--- | :--- |
| `fan_out_ratio` | `"High Fan-Out (Peel Chain Pattern)"` | Single input splitting rapidly into dozens of change/destination outputs |
| `unique_ips_used` | `"Rapid Multi-IP Broadcast"` | Wallet transactions broadcasted across numerous disparate IP nodes (sybil relay) |
| `total_volume_out` | `"Unusual Volume Surge (Outflow)"` | Sudden massive disbursement of funds far above baseline wallet activity |
| `total_volume_in` | `"Unusual Volume Surge (Inflow)"` | Sudden massive accumulation of funds far above baseline wallet activity |
| `fan_in_ratio` | `"High Fan-In (Mixer / Consolidation Pattern)"` | Numerous input addresses consolidating into a single output (CoinJoin/mixer) |
| `tx_count` | `"Abnormal Transaction Velocity"` | High burst velocity of transaction creation over observed interval |

#### Scoring & Explainability Methods
- `fit(X, feature_names=None)`: Fits unsupervised `IsolationForest(contamination=0.02, random_state=42, n_estimators=100)` and stores baseline population statistics (mean, std).
- `predict(X) -> np.ndarray`: Returns `-1` for anomalies and `+1` for normal inliers.
- `score_samples(X) -> np.ndarray`: Returns calibrated 0–100 risk scores strictly bounded in `[0.0, 100.0]`.
- `explain_instance(row) -> Dict[str, float]`: Computes feature attribution weights normalized so $\sum w_i = 1.0$. Handles zero-variance features and uniform datasets safely without division-by-zero.
- `get_top_factors(row, top_n=3) -> List[Tuple[str, str, float]]`: Returns `(feature_name, investigative_tag, weight)` for the highest-impact factors.
- `get_investigative_tags(row, top_n=3) -> List[str]`: Returns human-readable tags for the top risk factors.
- `get_anomaly_reason(row, top_n=2) -> str`: Produces a human-readable forensic summary string (e.g., `"Flagged due to: Rapid Multi-IP Broadcast (88.4%), Abnormal Transaction Velocity (11.2%)"`).
- `score_and_explain(X, anomaly_threshold=60.0, top_n=3) -> pd.DataFrame`: Directly attaches explainability metadata to the final scored wallet records:
  - `risk_score`: Float in `[0.0, 100.0]`
  - `is_anomaly`: Boolean (`True` if `risk_score >= anomaly_threshold` or `predict == -1`)
  - `top_risk_factors`: List of human-readable tags (guaranteed non-empty for anomalous wallets)
  - `top_features`: List of raw column names driving the risk score
  - `signal_breakdown`: Full normalized attribution dictionary
  - `reason`: Formatted forensic explanation string

### 3.4 True SHAP TreeExplainer Attribution Interface (`ml/explainer.py`)
Implemented by `ml/explainer.py:ShapExplainer` to compute true Shapley attribution values from fitted tree ensembles:

- **Model Integration**: Initializes `shap.TreeExplainer(model)` on the underlying fitted `IsolationForest` instance (either passed directly or unpacked from `IsolationForestAnomalyDetector`).
- **Dimension & Output Normalization**: Accurately handles single-output vs multi-output list responses and 2D/3D array representations across SHAP and scikit-learn versions (`(N, D)` shape guarantee).
- **100% Attribution Sum**: Computes absolute Shapley values $|s_j|$ and normalizes weights so $\sum w_j = 1.0$ (100%) per wallet, with floating-point residual adjustments guaranteeing exact closure.
- **Investigative Tag Mapping**: Direct mapping of top Shapley drivers to human-readable investigative tags (`"High Fan-Out (Peel Chain Pattern)"`, `"Rapid Multi-IP Broadcast"`, etc.).
- **Graceful Fallback & Performance Guard**: If SHAP is uninitialized, unfitted, or encounters uniform/zero-variance matrices, safely delegates to `IsolationForestAnomalyDetector.explain_instance()` or returns an exact uniform 100% attribution without division-by-zero or NaNs.

---

## 4. Implemented Pipeline Details

### 4.1 Ingestion Pipeline Stabilization (M2)
- **Multi-Format Ingestion**: Supports `.json` and `.csv`. In CSV ingestion, stringified array columns (`'["addr1", "addr2"]'`) are automatically deserialized via `json.loads`.
- **Missing Value & Schema Sanitization**: Null values in CSV entries (`fee`, `script_type`) are sanitized before Pydantic schema validation (`RawTransactionRow`).
- **Dynamic Offline GeoIP Resolution**: Searches candidate local paths for `GeoLite2-City.mmdb` (project root and `data/geolite2/`). Safely catches lookup exceptions for private/bogon IPs (e.g., `192.168.1.1`, `10.0.0.1`), falling back cleanly to `"UNKNOWN"`.

### 4.2 Feature Engineering Pipeline (M3)
- **List Unnesting & Alignment**: Unnests and aligns `input_addresses` with `input_amounts`, and `output_addresses` with `output_amounts`. Safely accounts for length discrepancies and stringified inputs.
- **Aggregation Metrics**: Accurately computes transaction counts, inflow volumes, outflow volumes, peel-chain/mixer ratios, and source IP diversity.
- **Sanitization & Scaling**: Division-by-zero, `NaN`, and `inf` are converted to `0.0`. Uses `StandardScaler` to produce model-ready numeric arrays. Empty and single-wallet DataFrames are handled gracefully.
- **Dual Interface Compatibility**: Retains `extract_features(df) -> (ip_features_df, wallet_features_df)` to maintain zero-regression backward compatibility with `backend/` and `graph/` components.

### 4.3 ML Model Training, Risk Scoring & Explainability Engine (M3)
- **Dual Input Compatibility**: Natively accepts either pandas DataFrames or normalized 2D NumPy arrays from `extract_wallet_features()`.
- **0–100 Risk Score Calibration**: Normalizes raw Isolation Forest decision offsets using baseline training distributions and batch metrics. Higher scores strictly denote higher threat risk (`100.0` = maximum anomaly, `0.0` = normal peer activity).
- **Outlier Discrimination**: Confirmed strong discrimination between standard 1-to-1 transactions (averaging $\sim 5$ score) and high fan-out peel chains ($\ge 85$ score) or multi-IP sybil relay broadcasters ($100.0$ score).
- **Zero-Latency Offline Attribution**: Uses population Z-score deviation relative to baseline with safe standard deviations (`safe_std = np.where(std > 1e-9, std, 1.0)`). Avoids heavy external runtime dependencies, providing sub-millisecond explanation generation per wallet.
- **Robust Edge-Case Guarding**: Guarantees clean handling of zero-variance features (e.g. constant `fan_out_ratio`) and completely uniform datasets without division-by-zero errors or NaNs.

### 4.4 True SHAP TreeExplainer Engine (M3)
- **Genuine Shapley Attribution**: Wraps `shap.TreeExplainer` over scikit-learn's `IsolationForest` estimators, calculating local tree-path Shapley values explaining why specific wallet vectors deviate from the expected ensemble decision surface.
- **Ground-Truth Outlier Identification**: Successfully isolates synthetic peel chains as dominated by `fan_out_ratio` (attributing $>45\%$ weight to peel patterns) and multi-IP sybil broadcasts as dominated by `unique_ips_used` (attributing dominant weight to multi-IP patterns).
- **Batch & Matrix Inference**: Supports `explain_instance(row)`, `explain_dataset(X)`, `get_top_factors(row, top_n)`, and `get_shap_matrix(X)` for both pandas DataFrames and raw NumPy arrays.

---

## 5. Instructions to Run Unit Tests

All tests are bound exclusively to the Linux virtual environment located at `/home/praneeth_tadi/.flashmen_env`.

### 5.1 Environment Activation & Command Invocation
Activate the virtual environment:
```bash
source /home/praneeth_tadi/.flashmen_env/bin/activate
```
Or directly invoke the interpreter:
```bash
/home/praneeth_tadi/.flashmen_env/bin/python -m pytest -v ml/tests/
```

### 5.2 Run Ingestion Tests
```bash
/home/praneeth_tadi/.flashmen_env/bin/python -m pytest -v ml/tests/test_ingestion.py
```

### 5.3 Run Feature Engineering Tests
```bash
/home/praneeth_tadi/.flashmen_env/bin/python -m pytest -v ml/tests/test_feature_engineering.py
```

### 5.4 Run Model Training, Risk Scoring & Explainability Tests
```bash
/home/praneeth_tadi/.flashmen_env/bin/python -m pytest -v -s ml/tests/test_model.py
```

### 5.5 Full Test Suite Execution Verification Log
```text
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /home/praneeth_tadi/.flashmen_env/bin/python
cachedir: .pytest_cache
rootdir: /mnt/c/Users/Praneeth Tadi/Documents/_SIH_bitcoin_traffic_monitor/flashmen
plugins: anyio-4.12.1
collecting ... collected 21 items

ml/tests/test_feature_engineering.py::test_wallet_volume_aggregation PASSED [  4%]
ml/tests/test_feature_engineering.py::test_fan_in_and_fan_out_ratios PASSED [  9%]
ml/tests/test_feature_engineering.py::test_scaled_matrix_dimensions_and_no_nan_inf PASSED [ 14%]
ml/tests/test_feature_engineering.py::test_unique_ips_used PASSED        [ 19%]
ml/tests/test_feature_engineering.py::test_empty_and_single_wallet_dataframe PASSED [ 23%]
ml/tests/test_features.py::test_extract_features_schema PASSED           [ 28%]
ml/tests/test_features.py::test_extract_features_empty_dataframe PASSED  [ 33%]
ml/tests/test_ingestion.py::test_process_raw_file_json PASSED            [ 38%]
ml/tests/test_ingestion.py::test_process_raw_file_csv PASSED             [ 42%]
ml/tests/test_ingestion.py::test_invalid_data_dropping PASSED            [ 47%]
ml/tests/test_model.py::test_isolation_forest_fit_predict PASSED         [ 52%]
ml/tests/test_model.py::test_isolation_forest_numpy_array_input PASSED   [ 57%]
ml/tests/test_model.py::test_risk_score_bounds_and_calibration PASSED    [ 61%]
ml/tests/test_model.py::test_synthetic_outlier_wallets_score_significantly_higher PASSED [ 66%]
ml/tests/test_model.py::test_signal_breakdown_attribution PASSED         [ 71%]
ml/tests/test_model.py::test_anomalous_wallets_return_top_risk_factors PASSED [ 76%]
ml/tests/test_model.py::test_injected_extreme_feature_attribution PASSED [ 80%]
ml/tests/test_model.py::test_attribution_edge_cases_zero_variance_and_uniform PASSED [ 85%]
ml/tests/test_model.py::test_shap_explainer PASSED                       [ 90%]
ml/tests/test_model.py::test_shap_explainer_synthetic_outlier_attribution PASSED [ 95%]
ml/tests/test_model.py::test_shap_explainer_edge_cases_and_matrix_inputs PASSED [100%]

============================== 21 passed in 7.76s ==============================
```
