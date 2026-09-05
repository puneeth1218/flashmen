# Project Context & Engineering Status: Bitcoin Traffic Monitor (Flashmen)

> **Repository**: `puneeth1218/flashmen`  
> **Role**: Senior Data & ML Engineer  
> **Status**: Milestones M1–M5 Fully Operational · Phase 2 (Real SHAP persistence, dynamic ego-graph traversal, deterministic sanctions engine, risk distribution chart) & Phase 3 (Real global search, live engine health badge, alert-to-graph cross-navigation) Verified  
> **Environment Support**: Dual Environment — Windows Local Virtual Environment (`.venv`) & Linux/WSL2 (`/home/praneeth_tadi/.flashmen_env`) · Clean passing test suite (`pytest ml/tests/` -> 21/21 passed, 100% pass rate)

---

## 1. Project Overview & SIH Challenge (PS 26146 - NTRO)

### 1.1 Scope & Problem Statement
Under **Smart India Hackathon (SIH) Problem Statement 26146 (NTRO)**, this project delivers an **offline-capable, explainable anomaly detection and network traffic monitoring platform for Bitcoin (P2P network layer & blockchain transaction layer)**.

The objective is to enable cyber intelligence, forensic investigators, and network analysts to:
- Ingest asynchronous, multi-format Bitcoin traffic dumps (JSON/CSV) without live internet dependencies.
- Correlate network-layer peer observations (IP addresses, ports, ASNs, GeoIP, timestamps) with on-chain ledger actions (transaction IDs, input/output wallet addresses, satoshi/BTC flow).
- Isolate suspicious entities (e.g., rapid peel-chaining, CoinJoin mixers, sybil relay clusters, high-fan-out wash trading, and anomalous port/burst velocities) using unsupervised machine learning and deterministic sanction blocklists.
- Provide explainable triage (local SHAP feature attributions, investigative reason tags) and interactive topological graph analysis (Cytoscape.js) to trace threat actors.

### 1.2 Core Operational Constraints
- **Air-Gapped & Offline Execution**: The entire pipeline operates in disconnected environments. GeoIP lookups utilize local MaxMind `.mmdb` databases (`data/geolite2/GeoLite2-City.mmdb`) with graceful fallback to `"UNKNOWN"`. All Python/Node dependencies are strictly pinned to exact versions in `requirements.txt` and `package.json` to guarantee reproducible behavior. Dependencies are locally packaged via `download_offline_packages.sh` / `.ps1` into `offline_packages/` prior to offline Docker execution.
- **Strict Non-Destructive Module Boundaries**: Unified interface contracts between data ingestion (`backend/services/ingestion.py`), machine learning (`ml/`), graph analytics (`graph/`), API routers (`backend/routers/`), and the frontend interface (`frontend/`).
- **Determinism & Performance**: Zero telemetry leaks, deterministic validation with Pydantic v2 schemas, vector-accelerated feature transforms in pandas/numpy, and lightweight ML scoring with low latency.

---

## 2. Active Architecture & Module Responsibilities

```
flashmen/
├── backend/                  # FastAPI Application & Services
│   ├── main.py               # Application factory & router mounts (CORS, lifespan, /health)
│   ├── database.py           # Fallback engine & session generator
│   ├── routers/              # API endpoints
│   │   ├── ingest.py         # POST /api/v1/ingest - raw traffic ingestion & pipeline execution
│   │   ├── alerts.py         # GET  /api/v1/alerts - paginated anomaly alerts with score/type filters
│   │   ├── stats.py          # GET  /api/v1/dashboard/stats - telemetry counters & real anomalous volume
│   │   ├── graph.py          # GET  /api/v1/graph - Cytoscape graph with dynamic ego-traversal
│   │   └── search.py         # GET  /api/v1/search - real polymorphic search across alerts & telemetry
│   └── services/
│       ├── database.py       # Synchronous SQLAlchemy engine (Alert model with shap_explanation JSON column)
│       ├── ingestion.py      # [M2] Raw CSV/JSON ingestion, Pydantic v2 validation, GeoIP enrichment
│       └── scoring.py        # [M3] Alert generation, ML inference, SHAP & OFAC Sanctions Rules Engine
├── data/
│   ├── geolite2/             # MaxMind offline GeoIP binary (GeoLite2-City.mmdb)
│   ├── synthetic/            # Synthetic sample files for testing (sample_traffic.csv)
│   └── alerts.db             # Local SQLite database fallback
├── offline_packages/         # Local cache for pip wheels and npm dependencies
│   ├── python/               # Downloaded Python wheels
│   └── npm/                  # Cached npm packages
├── download_offline_packages.sh/.ps1 # DevOps scripts to populate offline cache
├── frontend/                 # React 18 SPA (Vite + TypeScript + Tailwind + Cytoscape.js)
│   ├── src/
│   │   ├── components/       # Reusable components (Navbar, AlertTable, FileUpload, RiskDistributionChart)
│   │   │   └── graph/        # GraphViewer, NodeDetailPanel
│   │   ├── pages/            # DashboardPage, GraphPage, UploadPage
│   │   └── services/         # Typed Axios client (api.ts)
├── graph/                    # NetworkX graph construction & heuristic pattern matchers
│   ├── builder.py            # Directed multigraph construction for Cytoscape.js
│   └── heuristics.py         # Peel-chain & CoinJoin/mixer topological detectors
└── ml/                       # Machine Learning Pipeline
    ├── __init__.py           # Package exports (extract_wallet_features, IsolationForestAnomalyDetector, ShapExplainer)
    ├── dataset_gen.py        # 14-column synthetic dataset generator
    ├── explainer.py          # [M3] True SHAP TreeExplainer wrapper (genuine local Shapley attributions)
    ├── feature_engineering.py# [M3] List unnesting, wallet aggregations (6 metrics), scaling pipeline
    ├── model.py              # [M3] IsolationForestAnomalyDetector with 0-100 risk scoring & Z-score baseline
    └── tests/                # Automated pytest suite (21 passing unit tests)
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

### 3.4 True SHAP TreeExplainer & Feature Attribution Persistence
- `ml/explainer.py:ShapExplainer` calculates local tree-path Shapley values explaining why specific wallet vectors deviate from the expected ensemble decision surface.
- Normalizes absolute weights so $\sum w_j = 1.0$ (100%) per wallet.
- **Database Persistence**: Attributions are saved in `Alert.shap_explanation` (JSON column in `backend/services/database.py`), returned via `GET /api/v1/alerts`, and displayed in the frontend `AlertTable` details drawer.

### 3.5 Deterministic Sanctions Rules Engine (`backend/services/scoring.py`)
- Evaluates entities against known OFAC and Lazarus Group sanctioned addresses (e.g., `12qtT5...`, `1A1zP1...`, `bc1qa5...`).
- Guarantees immediate `100.0/100.0` risk score, `1.0` confidence, and `CRITICAL` alert tag bypassing ML contamination rates.

### 3.6 Dynamic Graph Traversal Contract (`backend/routers/graph.py`)
- Accepts `GET /api/v1/graph?entity_id=<id>&depth=<1..3>`.
- Builds a NetworkX directed multigraph, converts it to an undirected projection, and extracts subgraphs using `nx.ego_graph(G, entity_id, radius=depth)`.

### 3.7 Real Polymorphic Entity Search (`backend/routers/search.py`)
- Accepts `GET /api/v1/search?q=<query>`.
- Searches database `Alert` records for matching `entity_id` (returning risk score, confidence, and reason).
- Falls back to querying the latest ingested DataFrame in memory/disk for unflagged transactions or peer telemetry (returning `risk_score = 0.0`, `"Unflagged / Benign"`).

---

## 4. Instructions to Run Development Servers & Tests

> [!IMPORTANT]
> Always execute backend and ML commands from the **repository root directory (`flashmen/`)**.

### 4.1 Environment Activation

#### Windows (PowerShell):
```powershell
# From repository root:
.\.venv\Scripts\Activate.ps1
```

#### Linux / WSL2:
```bash
# From repository root:
source .venv/bin/activate
# Or if using dedicated Linux env:
source /home/praneeth_tadi/.flashmen_env/bin/activate
```

### 4.2 Run Backend Development Server
```bash
uvicorn backend.main:app --reload --port 8000
```
- OpenAPI Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/](http://localhost:8000/)

### 4.3 Run Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm run dev
```
- UI Dashboard: [http://localhost:5173](http://localhost:5173)

### 4.4 Run Automated Test Suite
From the repository root:
```bash
pytest ml/tests/
```

#### Verified Test Suite Results (21/21 passed):
```text
============================= test session starts ==============================
platform linux / win32 -- Python 3.11/3.13, pytest-9.1.1 -- 21 collected

ml/tests/test_feature_engineering.py::test_wallet_volume_aggregation PASSED
ml/tests/test_feature_engineering.py::test_fan_in_and_fan_out_ratios PASSED
ml/tests/test_feature_engineering.py::test_scaled_matrix_dimensions_and_no_nan_inf PASSED
ml/tests/test_feature_engineering.py::test_unique_ips_used PASSED
ml/tests/test_feature_engineering.py::test_empty_and_single_wallet_dataframe PASSED
ml/tests/test_features.py::test_extract_features_schema PASSED
ml/tests/test_features.py::test_extract_features_empty_dataframe PASSED
ml/tests/test_ingestion.py::test_process_raw_file_json PASSED
ml/tests/test_ingestion.py::test_process_raw_file_csv PASSED
ml/tests/test_ingestion.py::test_invalid_data_dropping PASSED
ml/tests/test_model.py::test_isolation_forest_fit_predict PASSED
ml/tests/test_model.py::test_isolation_forest_numpy_array_input PASSED
ml/tests/test_model.py::test_risk_score_bounds_and_calibration PASSED
ml/tests/test_model.py::test_synthetic_outlier_wallets_score_significantly_higher PASSED
ml/tests/test_model.py::test_signal_breakdown_attribution PASSED
ml/tests/test_model.py::test_anomalous_wallets_return_top_risk_factors PASSED
ml/tests/test_model.py::test_injected_extreme_feature_attribution PASSED
ml/tests/test_model.py::test_attribution_edge_cases_zero_variance_and_uniform PASSED
ml/tests/test_model.py::test_shap_explainer PASSED
ml/tests/test_model.py::test_shap_explainer_synthetic_outlier_attribution PASSED
ml/tests/test_model.py::test_shap_explainer_edge_cases_and_matrix_inputs PASSED

============================== 21 passed in ~7s ===============================
```
