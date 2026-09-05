# Backend Module Context & Implementation Status

> **Module**: `backend/`  
> **Status**: Fully Operational · Ingestion, Scoring, Graph Traversal, Persistence & Search Verified  
> **Framework**: FastAPI · Pydantic v2 · SQLAlchemy 2.0 · NetworkX · scikit-learn · SHAP  

---

## 1. Module Overview & Role
The `backend/` module serves as the central orchestration, database persistence, and API service layer for the **Bitcoin Traffic Monitor (Flashmen)** platform. It handles:
- Ingestion of raw offline transaction and network traffic files (CSV/JSON).
- Schema validation, data sanitization, and offline GeoIP enrichment.
- Deterministic sanctions rules matching (OFAC / Lazarus Group addresses).
- Unsupervised ML anomaly detection scoring (`IsolationForestAnomalyDetector`) and local feature attribution calculation (`ShapExplainer`).
- Dynamic ego-subgraph extraction with configurable hop depth (1–3) using NetworkX.
- Serving RESTful endpoints for the React frontend (alerts, graph topology, dashboard telemetry counters, and polymorphic entity search).

---

## 2. Directory Structure & File Contents

```
backend/
├── Dockerfile                # Multi-stage container definition using offline wheel caches
├── requirements.txt          # Python dependencies (pinned with scikit-learn, shap, networkx, geoip2)
├── main.py                   # Application entry point, CORS middleware, lifespan & router mounts
├── routers/                  # API route handlers
│   ├── __init__.py           # Package export exposing all 5 APIRouters
│   ├── ingest.py             # POST /api/v1/ingest - raw traffic file upload & end-to-end pipeline execution
│   ├── alerts.py             # GET  /api/v1/alerts - paginated anomaly alerts with SHAP explanations & filters
│   ├── stats.py              # GET  /api/v1/dashboard/stats - telemetry counters & real anomalous BTC volume
│   ├── graph.py              # GET  /api/v1/graph - Cytoscape network topology with dynamic ego-traversal
│   └── search.py             # GET  /api/v1/search - real polymorphic search across alerts & raw telemetry
└── services/                 # Business logic & contract implementations
    ├── __init__.py           # Service exports
    ├── database.py           # Synchronous SQLAlchemy engine, Alert ORM model with JSON shap_explanation & auto-migration
    ├── ingestion.py          # Contract 1 (M2): process_raw_file() with Pydantic v2 & GeoIP caching
    └── scoring.py            # Contract 2 (M3): score_entities() with ML inference, SHAP & Sanctions Rules Engine
```

---

## 3. What Has Been Implemented

### 3.1 Application Core (`main.py`, `services/database.py`)
- **FastAPI App Lifecycle**: Configured with asynchronous lifespan handler, auto-generated OpenAPI documentation (`/docs`), health check (`GET /`), and CORS middleware supporting frontend development origins (`http://localhost:3000`, `http://localhost:5173`).
- **Resilient Database Layer (`services/database.py`)**: 
  - SQLAlchemy 2.0 ORM engine supporting PostgreSQL with automatic, zero-configuration SQLite fallback (`sqlite:///./data/alerts.db`).
  - **`Alert` Model**: Persists `id`, `entity_type`, `entity_id`, `risk_score`, `confidence`, `reason`, `shap_explanation` (JSON column), and `created_at`.
  - **Automatic Migration**: Inspects existing SQLite/Postgres tables on startup and injects `shap_explanation` if missing.
  - Exposes reusable `get_db()` dependency generator.

### 3.2 Ingestion Engine (`services/ingestion.py`) — Milestone M2 (Verified)
- **Pydantic v2 Schema Enforcement**: `RawTransactionRow` validates incoming transaction records with UTC datetime parsing, IP address validation, and array typing.
- **Multi-Format Ingestion**: Handles raw JSON arrays and CSV files with stringified JSON lists (`json.loads` normalization).
- **Cached MaxMind GeoIP Enrichment**:
  - Offline lookup against `data/geolite2/GeoLite2-City.mmdb`.
  - In-memory `GEOIP_CACHE` avoids redundant disk reads for recurrent IP addresses.
  - Graceful fallback to `"UNKNOWN"` country code when database file is missing or IP is private/loopback.

### 3.3 Scoring & Intelligence Engine (`services/scoring.py`) — Milestone M3 (Verified)
- **Deterministic Rules Engine**: Matches entities against `SANCTIONED_ENTITIES` (e.g. OFAC/Lazarus Group addresses). Flags matches immediately with `risk_score=100.0`, `confidence=1.0`, and `"CRITICAL: Sanctioned Entity / Known Threat Actor"`.
- **ML Anomaly Inference**: Feeds extracted wallet features (`extract_wallet_features`) into `IsolationForestAnomalyDetector` to compute calibrated 0–100 risk scores.
- **SHAP Feature Attribution**: Generates local feature contributions via `ShapExplainer` and persists the attribution dictionary into `Alert.shap_explanation`.

### 3.4 Dynamic Graph Traversal (`routers/graph.py`)
- Ingests raw traffic records into `NetworkGraphBuilder`.
- When an `entity_id` is supplied, converts the multigraph into an undirected projection and extracts subgraphs using `nx.ego_graph(G, entity_id, radius=depth)`.
- Serializes graph into standard Cytoscape-compliant JSON (`nodes` and `edges`).

### 3.5 Real Polymorphic Entity Search (`routers/search.py`)
- Accepts search query parameter `q`.
- First queries the `Alert` database table for matching `entity_id` (case-insensitive substring match).
- If unflagged, falls back to querying the latest in-memory/disk DataFrame for raw transaction hashes or peer IP activity (returning `risk_score=0.0`, `"Unflagged / Benign"`).

### 3.6 Real Anomalous Volume Computation (`routers/stats.py`)
- Computes real BTC volume from transactions associated with anomalous entities (`risk_score >= 60.0`), replacing heuristic approximations.

---

## 4. Setup & Running Instructions

> [!IMPORTANT]
> Always execute backend commands from the **repository root (`flashmen/`)** so that `backend`, `ml`, and `graph` imports resolve cleanly.

```bash
# 1. Activate environment (from root)
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/](http://localhost:8000/)

