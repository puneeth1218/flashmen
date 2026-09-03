# Project Context & Engineering Status: Bitcoin Traffic Monitor (Flashmen)

> **Repository**: `puneeth1218/flashmen`  
> **Role**: Senior Data & ML Engineer  
> **Status**: Milestone M2 (Ingestion) Stabilized · Milestone M3 (Feature Engineering) Implemented & Verified  
> **Environment Status**: Clean passing test suite (`python -m pytest -v ml/tests/` -> 12 passed)  

---

## 1. Project Overview & SIH Challenge (PS 26146 - NTRO)

### 1.1 Scope & Problem Statement
Under **Smart India Hackathon (SIH) Problem Statement 26146 (NTRO)**, this project delivers an **offline-capable, explainable anomaly detection and network traffic monitoring platform for Bitcoin (P2P network layer & blockchain transaction layer)**.

The objective is to enable cyber intelligence, forensic investigators, and network analysts to:
- Ingest asynchronous, multi-format Bitcoin traffic dumps (JSON/CSV) without live internet dependencies.
- Correlate network-layer peer observations (IP addresses, ports, ASNs, GeoIP, timestamps) with on-chain ledger actions (transaction IDs, input/output wallet addresses, satoshi/BTC flow).
- Isolate suspicious entities (e.g., rapid peel-chaining, CoinJoin mixers, sybil relay clusters, high-fan-out wash trading, and anomalous port/burst velocities) using unsupervised machine learning.
- Provide explainable triage (SHAP feature attributions) and interactive topological graph analysis (Cytoscape.js) to trace threat actors.

### 1.2 Core Operational Constraints
- **Air-Gapped & Offline Execution**: The entire pipeline operates in disconnected environments. GeoIP lookups utilize local MaxMind `.mmdb` databases (`data/geolite2/GeoLite2-City.mmdb`) with graceful fallback to `"UNKNOWN"`. All Python/Node dependencies are strictly pinned to exact versions in `requirements.txt` and `package.json` to guarantee reproducible behavior. Dependencies are locally packaged via `download_offline_packages.sh` / `.ps1` into `offline_packages/` prior to offline Docker execution.
- **Strict Non-Destructive Module Boundaries**: Parallel development requires isolating changes strictly to data ingestion (`backend/services/ingestion.py`) and machine learning (`ml/`), preserving existing contracts and avoiding touching `backend/routes/`, `frontend/`, or `graph/`.
- **Determinism & Performance**: Zero telemetry leaks, deterministic validation with Pydantic v2 schemas, vector-accelerated feature transforms in pandas/numpy, and lightweight ML scoring.

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
├── offline_packages/         # Local cache for pip wheels and npm dependencies
├── download_offline_packages.sh/.ps1 # DevOps scripts to populate offline cache
├── frontend/                 # React 18 SPA (Vite + TypeScript + Tailwind + Cytoscape.js)
├── graph/                    # NetworkX graph construction & heuristic pattern matchers
│   ├── builder.py            # Directed multigraph construction for Cytoscape.js
│   └── heuristics.py         # Peel-chain & CoinJoin/mixer topological detectors
└── ml/                       # Machine Learning Pipeline
    ├── __init__.py           # Package exports (extract_wallet_features, extract_features, etc.)
    ├── dataset_gen.py        # 14-column synthetic dataset generator
    ├── explainer.py          # SHAP TreeExplainer wrapper for alert explainability
    ├── feature_engineering.py# [M3] List unnesting, wallet aggregations, scaling pipeline
    ├── model.py              # IsolationForest wrapper with 0-100 risk scoring
    └── tests/                # Automated pytest suite
        ├── test_feature_engineering.py # M3 wallet metrics & scaling tests
        ├── test_features.py            # Legacy dual-feature compatibility tests
        ├── test_ingestion.py           # M2 JSON/CSV parsing & GeoIP fallback tests
        └── test_model.py               # Isolation Forest & SHAP unit tests
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

---

## 5. Instructions to Run Unit Tests

All tests are designed to execute fully offline within Conda, WSL, or Windows PowerShell.

### 5.1 Run Ingestion Tests
```bash
python -m pytest -v ml/tests/test_ingestion.py
```

### 5.2 Run Feature Engineering Tests
```bash
python -m pytest -v ml/tests/test_feature_engineering.py
```

### 5.3 Run Full ML Suite
```bash
python -m pytest -v ml/tests/
```

### 5.4 Test Execution Verification Log
```
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
