# Flashmen (Bitcoin Traffic Monitor)

A production-ready monorepo for real-time Bitcoin network traffic analysis, anomaly detection, explainable AI, and interactive graph visualization. Built under Smart India Hackathon (SIH) Problem Statement 26146 (NTRO).

Powered by **FastAPI**, **React (Vite + TypeScript + Tailwind CSS)**, **IsolationForest ML**, **SHAP TreeExplainer**, and **NetworkX** graph analytics.

---

## 📁 Repository Structure

```
flashmen/
├── docker-compose.yml              # Multi-container orchestration (PostgreSQL 15, FastAPI, React/Nginx)
├── README.md                       # Master setup guide & environment documentation
├── context.md                      # Comprehensive project status & architectural contracts
├── description.md                  # Detailed system capabilities & milestone achievements
├── requirements.txt                # Root Python dependencies (FastAPI, scikit-learn, SHAP, NetworkX, GeoIP2)
├── download_offline_packages.sh    # Linux/macOS offline wheel & npm cache downloader
├── download_offline_packages.ps1   # Windows PowerShell offline wheel & npm cache downloader
├── offline_packages/               # Cached pip wheels and npm tarballs for air-gapped deployment
│   ├── python/                     # Downloaded Python wheels
│   └── npm/                        # Cached npm packages
├── data/
│   ├── geolite2/                   # Offline MaxMind GeoIP database (GeoLite2-City.mmdb)
│   ├── synthetic/                  # Synthetic test datasets (sample_traffic.csv)
│   └── alerts.db                   # Local SQLite database fallback
├── backend/                        # FastAPI REST API & database persistence
│   ├── Dockerfile                  # Offline-capable multi-stage backend container
│   ├── main.py                     # FastAPI app factory, CORS, lifespan handler, router mounts
│   ├── routers/                    # REST API controllers
│   │   ├── ingest.py               # POST /api/v1/ingest - CSV/JSON traffic ingestion & pipeline execution
│   │   ├── alerts.py               # GET /api/v1/alerts - Paginated alerts with score/type filtering
│   │   ├── stats.py                # GET /api/v1/dashboard/stats - Real-time network telemetry counters
│   │   ├── graph.py                # GET /api/v1/graph - Cytoscape graph with dynamic ego-traversal
│   │   └── search.py               # GET /api/v1/search - Real polymorphic search across entities & telemetry
│   └── services/                   # Core business logic
│       ├── database.py             # SQLAlchemy ORM (Alert model, Postgres/SQLite, SHAP auto-migration)
│       ├── ingestion.py            # M2: Pydantic v2 validation, GeoIP enrichment, CSV/JSON parser
│       └── scoring.py              # M3: ML inference, SHAP generation & OFAC Sanctions Rules Engine
├── ml/                             # Machine Learning & Explainable AI
│   ├── feature_engineering.py      # M3: List unnesting, wallet aggregation (6 metrics), StandardScaler
│   ├── model.py                    # M3: IsolationForestAnomalyDetector (0-100 risk scores, forensic tags)
│   ├── explainer.py                # M3: Real SHAP TreeExplainer wrapper (normalized 100% local attributions)
│   ├── dataset_gen.py              # Synthetic Bitcoin traffic generator (peel-chains, mixers, sybil relays)
│   └── tests/                      # Pytest unit test suite (21 passing tests)
├── graph/                          # NetworkX topological analytics
│   ├── builder.py                  # Directed Multigraph construction & Cytoscape.js serialization
│   └── heuristics.py               # On-chain heuristic matchers (Peel-chain, CoinJoin mixer detection)
└── frontend/                       # React 18 SPA (Vite + TypeScript + Tailwind CSS)
    ├── package.json                # Frontend dependencies (Lucide icons, Cytoscape, React Query)
    ├── Dockerfile                  # Production Nginx container build
    ├── vite.config.ts              # Vite configuration with API reverse proxy
    └── src/
        ├── App.tsx                 # Root layout & routing configuration
        ├── components/             # Reusable UI components
        │   ├── Navbar.tsx          # Aceternity dark header with global search (⌘K) & live health indicator
        │   ├── AlertTable.tsx      # High-contrast triage table with SHAP inspection drawer
        │   ├── FileUpload.tsx      # Drag-and-drop CSV/JSON ingestion zone (Route: /upload)
        │   ├── StatsSummary.tsx    # Telemetry metrics grid (Transactions, Volume, Peers)
        │   ├── RiskDistributionChart.tsx # SVG risk score distribution histogram
        │   └── graph/              # Cytoscape Graph components (GraphViewer, NodeDetailPanel)
        ├── pages/                  # Application views (DashboardPage, GraphPage, UploadPage)
        └── services/               # Typed Axios API client (api.ts)
```

---

## ⚙️ Quick Start with Docker (Recommended)

Start the entire stack (PostgreSQL, Backend API, and Frontend UI) with a single command:

```bash
docker compose up --build
```
*(Or `docker-compose up --build` on older Docker versions)*

### Service Endpoints:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/](http://localhost:8000/)
- **PostgreSQL Database**: `localhost:5432` (`btm_user` / `btm_password` / `bitcoin_traffic_monitor`)

---

## 🛠️ Local Manual Development Setup

> [!IMPORTANT]
> **Always execute Python commands from the repository root directory (`flashmen/`)**.  
> The backend imports modules across `backend`, `ml`, and `graph`. Running from the root ensures all module imports resolve correctly without needing custom path hacks.

### 1. Python Environment Setup (Backend & ML)

#### On Windows (PowerShell):
```powershell
# From the repository root:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install all dependencies:
pip install -r requirements.txt
```

#### On Linux / macOS:
```bash
# From the repository root:
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies:
pip install -r requirements.txt
```

### 2. GeoLite2 Offline Database (Optional but Recommended)
Place your `GeoLite2-City.mmdb` file in:
```
data/geolite2/GeoLite2-City.mmdb
```
*(If omitted, the ingestion service automatically falls back to `"UNKNOWN"` country codes without errors).*

### 3. Generate Synthetic Test Data
Generate a realistic 500-row Bitcoin traffic dataset with simulated peel chains and mixer patterns:
```bash
python -m ml.dataset_gen --output data/synthetic/sample_traffic.csv --rows 500
```

### 4. Run Automated ML & Ingestion Tests
```bash
pytest ml/tests/
```
*(Runs all 21 unit tests across ingestion, feature engineering, Isolation Forest scoring, and SHAP explainability).*

### 5. Start Backend Development Server
```bash
# Run from repository root:
uvicorn backend.main:app --reload --port 8000
```
- API Documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Automatically uses SQLite (`sqlite:///./data/alerts.db`) when `DATABASE_URL` is not set.

### 6. Start Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- Vite dev server will start at: [http://localhost:5173](http://localhost:5173)
- Automatically proxies `/api` calls to `http://localhost:8000`.

---

## 📦 Offline & Air-Gapped Operation Instructions

For deployment in fully air-gapped or restricted network environments (SIH 26146 evaluation):

### Step 1: Pre-download Dependencies (On Internet-Connected Machine)
Execute the helper script to populate `offline_packages/`:
- **Linux/macOS**:
  ```bash
  chmod +x download_offline_packages.sh
  ./download_offline_packages.sh
  ```
- **Windows (PowerShell)**:
  ```powershell
  .\download_offline_packages.ps1
  ```

### Step 2: Install Offline (On Air-Gapped Machine)

#### Python Backend:
```bash
pip install --no-index --find-links=offline_packages/python -r requirements.txt
```

#### Frontend Node Packages:
```bash
cd frontend
npm ci --cache ../offline_packages/npm --prefer-offline
```

#### Offline Docker Build:
```bash
docker compose build
docker compose up
```

---

## 🔬 Core System Capabilities

1. **Multi-Format Ingestion**: Ingests raw JSON/CSV network dumps with Pydantic v2 validation, UTC normalization, and cached MaxMind GeoIP resolution.
2. **Deterministic Rules Engine**: Instant 100/100 risk score and critical alert generation for sanctioned threat actors (OFAC / Lazarus Group addresses).
3. **Unsupervised ML Anomaly Detection**: `IsolationForestAnomalyDetector` generates calibrated 0–100 risk scores based on 6 aggregated wallet metrics.
4. **Real SHAP Explainability**: True TreeExplainer feature attributions stored directly in PostgreSQL/SQLite (`shap_explanation` JSON column) and visualizable via interactive drawers in the UI.
5. **Dynamic Subgraph Traversal**: NetworkX-powered ego-graph extraction supporting 1 to 3 hops from any selected entity.
6. **Global Search**: Instant search across flagged database alerts and raw transaction telemetry with keyboard navigation (`⌘K` / `/`).
7. **Aceternity Dark Mode Interface**: Modern high-contrast dark aesthetic with real-time backend health polling and interactive risk distribution histograms.

---

## 👥 Team Workstreams & Code Ownership

| Role | Area | Core Modules |
| :--- | :--- | :--- |
| **Team Lead / DevOps** | Infra & Orchestration | `docker-compose.yml`, `offline_packages/`, `.github/` |
| **Backend Engineer 1** | Ingestion & Schema | `backend/services/ingestion.py`, `backend/routers/ingest.py` |
| **Backend Engineer 2** | Persistence & APIs | `backend/services/database.py`, `backend/routers/alerts.py`, `stats.py`, `search.py` |
| **ML Engineer 1** | Feature Engineering & Model | `ml/feature_engineering.py`, `ml/model.py`, `ml/dataset_gen.py` |
| **ML Engineer 2** | SHAP & Rules Engine | `ml/explainer.py`, `backend/services/scoring.py` |
| **Graph & Frontend Eng** | Network Topology & UI | `graph/builder.py`, `graph/heuristics.py`, `frontend/` |
