# Bitcoin Traffic Monitor — Project Description

> **Status**: Production-Ready · All 3 Interface Contracts, Phase 2 & Phase 3 Verified  
> **Challenge**: Smart India Hackathon (SIH) Problem Statement 26146 (NTRO)  
> **Environment Support**: Windows Local Virtual Environment (`.venv`) & Linux/WSL2  

---

## 1. Executive Summary

A high-performance, explainable cyber intelligence platform for **real-time Bitcoin network traffic analysis, anomaly detection, and topological graph visualization**. It correlates network-layer P2P peer activity with blockchain transaction ledger flows to detect and isolate suspicious threat actors (peel chains, CoinJoin mixers, sybil relays, wash trading, and OFAC/sanctioned wallets).

Built with **FastAPI**, **React 18 (Vite + TypeScript + Tailwind CSS)**, **IsolationForest ML**, **SHAP TreeExplainer**, and **NetworkX** graph analytics.

---

## 2. Implemented Architecture & Components

### 2.1 Root Infrastructure & DevOps

| File / Directory | Operational Role |
| :--- | :--- |
| `docker-compose.yml` | Orchestrates 3 services (PostgreSQL 15, FastAPI backend, and React/Nginx frontend) with health checks and volume mounts. |
| `requirements.txt` | Pinned Python dependencies for root and container environments. |
| `download_offline_packages.sh` / `.ps1` | Automation scripts to download Python wheels and npm packages into local cache for air-gapped environments. |
| `offline_packages/` | Directory holding cached pip wheels and npm tarballs for 100% offline deployment. |
| `README.md` | Master setup guide with Docker, manual local dev, offline installation, and team workstreams. |
| `context.md` | In-depth engineering context, schema contracts, and milestone tracking. |

### 2.2 Backend Service Layer (`backend/`)

- **FastAPI Core (`backend/main.py`)**: Asynchronous lifespan handler, CORS middleware, auto-generated OpenAPI documentation (`/docs`), health check (`GET /`).
- **Database Persistence (`backend/services/database.py`)**: Synchronous SQLAlchemy 2.0 ORM supporting PostgreSQL and automatic SQLite fallback (`sqlite:///./data/alerts.db`). Auto-migrates database schemas to ensure the JSON `shap_explanation` column exists.
- **REST Endpoints (`backend/routers/`)**:
  - `POST /api/v1/ingest`: Receives raw CSV/JSON dumps, executes validation and scoring pipelines, and persists flagged entities with SHAP attributions into the database.
  - `GET /api/v1/alerts`: Returns paginated alerts with entity type (`wallet` / `ip`) and minimum score filtering, complete with stored SHAP explanation weights.
  - `GET /api/v1/dashboard/stats`: Returns telemetry counters, active peer count, risk score histogram bins, and real anomalous BTC volume.
  - `GET /api/v1/graph`: Cytoscape-compliant network topology with dynamic ego-graph depth traversal (1–3 hops).
  - `GET /api/v1/search`: Polymorphic search querying database alerts first, falling back to in-memory/disk telemetry for unflagged entities.
- **Business Logic (`backend/services/`)**:
  - `ingestion.py`: Pydantic v2 validation, UTC normalization, and cached offline MaxMind GeoLite2 enrichment.
  - `scoring.py`: Orchestrates ML feature extraction, Isolation Forest scoring, SHAP explainability, and the deterministic OFAC Sanctions Rules Engine.

### 2.3 Machine Learning & Explainability (`ml/`)

| File | Operational Role |
| :--- | :--- |
| `feature_engineering.py` | Extracts 6 aggregate wallet metrics (`tx_count`, `total_volume_in`, `total_volume_out`, `fan_out_ratio`, `fan_in_ratio`, `unique_ips_used`) and scales them via `StandardScaler`. |
| `model.py` | `IsolationForestAnomalyDetector` provides calibrated 0–100 risk scoring, outlier discrimination, and baseline population Z-score explainability. |
| `explainer.py` | `ShapExplainer` wraps scikit-learn IsolationForest with `shap.TreeExplainer`, producing normalized 100% feature attributions mapped to human-readable forensic tags. |
| `dataset_gen.py` | CLI dataset generator for realistic Bitcoin P2P and ledger telemetry with injected anomalies. |
| `tests/` | Automated unit test suite (21 passing tests covering ingestion, features, model fitting, and SHAP). |

### 2.4 Graph Analytics (`graph/`)

| File | Operational Role |
| :--- | :--- |
| `builder.py` | `NetworkGraphBuilder` and `build_cytoscape_graph()` convert traffic records into directed multigraphs serialized to Cytoscape JSON (`nodes` and `edges`). |
| `heuristics.py` | On-chain heuristic detectors for peel chains (1-input-2-output change address patterns) and CoinJoin mixers (≥3 inputs and ≥3 outputs). |

### 2.5 Frontend User Interface (`frontend/`)

- **Design System**: Aceternity UI dark mode (`#000000` canvas, `zinc-950` cards, 1px crisp borders, ghost pills).
- **Core Components**:
  - `Navbar.tsx`: Sticky frosted header with global search shortcut (`⌘K` / `/`), autocomplete dropdown, and live backend health indicator.
  - `AlertTable.tsx`: Interactive triage table with risk badges, persistent storage across page refreshes, and expandable SHAP explainability drawer.
  - `RiskDistributionChart.tsx`: SVG histogram visualizing risk score distribution across 5 buckets.
  - `StatsSummary.tsx`: Telemetry counters for transactions, anomalous BTC volume, monitored entities, and active peers.
  - `FileUpload.tsx`: Drag-and-drop CSV/JSON ingestion zone with inline progress and response summaries.
  - `graph/GraphViewer.tsx`: Interactive Cytoscape.js network canvas with COSE layout, node details drawer, and depth selector.
- **Pages**: `DashboardPage.tsx`, `GraphPage.tsx`, `UploadPage.tsx`.

---

## 3. Verified Interface Contracts

```text
[Contract 1] process_raw_file      → Ingests multi-format CSV/JSON with MaxMind GeoIP fallback   ✅
[Contract 2] score_entities        → Produces AlertData with 0-100 risk & real SHAP attributions  ✅
[Contract 3] build_cytoscape_graph → Serializes dual-layer multigraph to Cytoscape JSON          ✅
```

---

## 4. Environment & Local Setup Commands

> [!IMPORTANT]
> **Always run Python and ML commands from the repository root (`flashmen/`)**.

### Backend & ML Setup:
```bash
# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run ML test suite (21/21 passed)
pytest ml/tests/

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Dev server starts at `http://localhost:5173` (proxies `/api` to `http://localhost:8000`).

### Docker Compose (Full Stack):
```bash
docker compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

