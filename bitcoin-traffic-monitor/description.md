# Bitcoin Traffic Monitor — Project Description

> **Status**: Scaffold Complete · All 3 Interface Contracts Verified  
> **Last Updated**: 2026-09-02

---

## What Is This?

A hackathon monorepo for **real-time Bitcoin network traffic analysis, anomaly detection, and graph visualization**. It combines network-layer P2P traffic monitoring with blockchain transaction analysis to flag suspicious entities (IP addresses and wallet addresses) using machine learning and graph heuristics.

---

## What Has Been Built

### 1. Root Infrastructure & DevOps

| File | What It Does |
|------|-------------|
| `docker-compose.yml` | Orchestrates 3 services — PostgreSQL 15, FastAPI backend, React frontend — with health checks, volume mounts, and environment variable injection |
| `.env.example` | Template for database credentials, GeoLite2 path, API host/port, and Vite base URL |
| `.github/CODEOWNERS` | Maps repository paths to 6 team members (DevOps, Backend ×2, ML ×2, Graph/Frontend) |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline — runs Flake8 linting + Pytest on Python modules, and npm build on the frontend |
| `offline_packages/` | Directory for caching pip wheels and npm tarballs for air-gapped environments |
| `README.md` | Full setup guide with Docker, manual local dev, offline installation, and team role table |

---

### 2. Backend — FastAPI (`backend/`)

**Entry point**: `main.py` — FastAPI app with CORS middleware (allowing `localhost:3000` and `:5173`), async lifespan handler, and 5 API routers mounted.

**Database**: `database.py` — SQLAlchemy 2.0 engine with PostgreSQL support and automatic SQLite fallback for local development. Exposes a `get_db()` dependency generator.

**API Endpoints**:

| Route | Method | File | Description |
|-------|--------|------|-------------|
| `/api/v1/ingest` | POST | `routers/ingest.py` | Accepts CSV/JSON file upload, saves to disk, runs `process_raw_file()` → `score_entities()` pipeline, returns record count + alert count |
| `/api/v1/alerts` | GET | `routers/alerts.py` | Paginated alert listing with `min_score` and `entity_type` filters. Returns `PaginatedAlertResponse` with total, page, limit, and alert array |
| `/api/v1/dashboard/stats` | GET | `routers/stats.py` | Dashboard summary — total transactions, high/medium risk counts, active peers, risk score histogram, top flagged countries |
| `/api/v1/graph` | GET | `routers/graph.py` | Returns Cytoscape-compliant JSON with typed Pydantic models (`NodeData`, `EdgeData`). Supports `entity_id` focus and `depth` parameter |
| `/api/v1/search` | GET | `routers/search.py` | Global entity search across IPs, wallets, and transaction hashes. Auto-detects entity type from query format |

**Service Layer (Interface Contracts)**:

| File | Contract | Signature |
|------|----------|-----------|
| `services/ingestion.py` | **Contract 1 (M2→M1)** | `process_raw_file(filepath: str) -> pd.DataFrame` — Parses CSV/JSON, fills missing columns with defaults, returns exactly 14 columns: `timestamp, src_ip, dst_ip, src_port, dst_port, txid, input_addresses, output_addresses, input_amounts, output_amounts, src_asn, src_country, dst_asn, dst_country` |
| `services/scoring.py` | **Contract 2 (M3→M1)** | `score_entities(df: pd.DataFrame) -> List[AlertData]` — Extracts unique IPs and wallets, returns `AlertData` Pydantic objects with `entity_type` (wallet\|ip), `entity_id`, `risk_score` (0–100), `confidence` (0–1), `reason`, and `shap_explanation` dict |

---

### 3. Machine Learning Module (`ml/`)

| File | What It Does |
|------|-------------|
| `feature_engineering.py` | `extract_features(df) -> (ip_features_df, wallet_features_df)` — Computes per-IP metrics (connection count, fan-out ratio, unique ports, non-standard port ratio) and per-wallet metrics (tx count, total BTC sent, peel-chain depth, equal output ratio, CoinJoin participation) |
| `model.py` | `IsolationForestAnomalyDetector` class — wraps scikit-learn's IsolationForest with `fit()`, `predict()` (returns -1/+1 labels), and `score_samples()` (returns normalized 0–100 risk scores). Configured with `contamination=0.05`, 100 estimators |
| `explainer.py` | `ShapExplainer` class — `explain_instance(feature_row) -> Dict[str, float]` — generates normalized feature attribution values summing to ~1.0 using Dirichlet distribution (stub for real SHAP TreeExplainer integration) |
| `dataset_gen.py` | CLI tool: `python ml/dataset_gen.py --output path.csv --count 500` — generates synthetic traffic records with Faker IPs, random ASNs, country codes, Bitcoin address stubs, and 64-char hex transaction IDs |
| `tests/test_features.py` | Pytest — validates feature extraction output schema and empty DataFrame handling |
| `tests/test_model.py` | Pytest — validates IsolationForest fit/predict/score cycle returns correct shapes and value ranges, and SHAP explainer returns proper dict structure |

---

### 4. Graph Analytics Module (`graph/`)

| File | What It Does |
|------|-------------|
| `builder.py` | **Contract 3 (M4→M5)**: `build_cytoscape_graph(df) -> Dict` — builds a directed NetworkX graph from traffic records (IP nodes, wallet nodes, transaction nodes; P2P traffic edges, input/output edges) and serializes to Cytoscape JSON: `{"nodes": [{"data": {"id", "label", "type"}}], "edges": [{"data": {"id", "source", "target", "label", "amount"}}]}`. Also exposes `NetworkGraphBuilder` class for incremental graph construction |
| `heuristics.py` | `detect_peel_chains(df) -> List[Dict]` — identifies 1-input-2-output transaction patterns (change address heuristic). `detect_mixers(df) -> List[Dict]` — identifies ≥3-input ≥3-output CoinJoin structures. Both return pattern descriptors with confidence scores |

---

### 5. Frontend — React + Vite + TypeScript (`frontend/`)

**Configuration**: Vite dev server on port 3000 with `/api` proxy to `localhost:8000`. TailwindCSS for styling. TypeScript strict mode.

**Dependencies**: React 18, React Router v6, Axios, Cytoscape.js + react-cytoscapejs, Lucide React icons.

**API Client** (`src/services/api.ts`):  
Fully typed Axios bindings with TypeScript interfaces mirroring all backend Pydantic models — `AlertData`, `PaginatedAlertResponse`, `DashboardStats`, `CytoscapeGraphResponse`, `IngestResponse`, `SearchResponse`. Exports 5 functions: `fetchAlerts()`, `fetchDashboardStats()`, `fetchNetworkGraph()`, `uploadTrafficFile()`, `globalSearch()`.

**Components**:

| Component | Description |
|-----------|-------------|
| `Navbar.tsx` | Top navigation bar with logo, global search input (routes to Graph page), and nav links (Dashboard, Graph Explorer, Ingest Logs) |
| `StatsSummary.tsx` | 4-card metric grid — Total Transactions, High Risk Alerts, Monitored Entities, Active P2P Peers — with Lucide icons and color coding |
| `AlertTable.tsx` | Sortable data table with risk-score color badges (red ≥75, amber ≥40, green <40), entity type badges (purple=wallet, blue=IP), and expandable SHAP feature attribution panel on row click |
| `GraphViewer.tsx` | Cytoscape.js network graph viewer with node-type styling (green ellipse=IP, purple rectangle=wallet, red border=high risk), edge arrows, COSE layout, and legend |

**Pages**:

| Page | Route | Description |
|------|-------|-------------|
| `DashboardPage.tsx` | `/` | Loads stats + alerts from API, renders StatsSummary cards + AlertTable |
| `GraphPage.tsx` | `/graph` | Loads Cytoscape graph data with optional search entity focus and depth selector (1–3 hops) |
| `UploadPage.tsx` | `/upload` | File upload form (CSV/JSON/JSONL) with drag-drop zone, progress feedback, and success/error result display |

---

### 6. Generated Data

| File | Content |
|------|---------|
| `data/synthetic/sample_traffic.csv` | 50 synthetic Bitcoin traffic records with all 14 contract columns — generated by `ml/dataset_gen.py` |

---

## Verification Results

All Python files pass `py_compile`. All 3 interface contracts verified end-to-end:

```
[Contract 1] process_raw_file     → 50 rows, 14 columns                    ✅
[Contract 2] score_entities       → 40 AlertData objects (risk 0-100)       ✅
[Contract 3] build_cytoscape_graph→ 240 nodes, 150 edges (Cytoscape JSON)  ✅
```

---

## Total File Count

| Module | Files |
|--------|-------|
| Root config | 5 |
| Data directories | 3 |
| Backend | 12 |
| ML | 7 |
| Graph | 3 |
| Frontend | 13 |
| **Total** | **43** |
