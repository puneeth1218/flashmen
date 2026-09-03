# Backend Module Context & Implementation Status

> **Module**: `backend/`  
> **Status**: Scaffolding Complete · Ingestion Pipeline Verified (Milestone M2)  
> **Framework**: FastAPI · Pydantic v2 · SQLAlchemy 2.0  

---

## 1. Module Overview & Role
The `backend/` module serves as the central orchestration and API service layer for the **Bitcoin Traffic Monitor (Flashmen)** platform. It handles:
- Ingestion of raw offline transaction and network traffic files (CSV/JSON).
- Schema validation, data sanitization, and GeoIP enrichment.
- Serving RESTful endpoints for the React frontend (alerts, graph topology, dashboard telemetry, and global entity search).
- Interfacing with the ML inference engine and graph analytics pipelines.

---

## 2. Directory Structure & File Contents

```
backend/
├── Dockerfile                # Multi-stage container definition, updated to build exclusively from local `offline_packages/`
├── requirements.txt          # Python dependencies (strictly pinned with `==` for deterministic offline builds)
├── database.py               # Database engine & session generator (PostgreSQL + SQLite fallback)
├── main.py                   # Application entry point, CORS middleware, lifespan & router mounts
├── routers/                  # API route handlers
│   ├── __init__.py           # Package export exposing all 5 APIRouters
│   ├── ingest.py             # POST /api/v1/ingest - raw traffic file upload & ingestion
│   ├── alerts.py             # GET  /api/v1/alerts - paginated anomaly alerts with score/type filters
│   ├── stats.py              # GET  /api/v1/dashboard/stats - telemetry counters & risk distribution
│   ├── graph.py              # GET  /api/v1/graph - Cytoscape-compliant network topology
│   └── search.py             # GET  /api/v1/search - polymorphic search across IPs, wallets, and txids
└── services/                 # Business logic & contract implementations
    ├── __init__.py           # Service exports
    ├── ingestion.py          # Contract 1 (M2): process_raw_file() with Pydantic & GeoIP caching
    └── scoring.py            # Contract 2 (M3): score_entities() stub returning AlertData models
```

---

## 3. What Has Been Implemented By This Point

### 3.1 Application Core (`main.py`, `database.py`)
- **FastAPI App Scaffolding**: Configured with asynchronous lifespan handler, auto-generated OpenAPI documentation (`/docs`), and CORS middleware supporting frontend development origins (`http://localhost:3000`, `http://localhost:5173`).
- **Resilient Database Layer (`database.py`)**: Configured via SQLAlchemy 2.0 engine targeting PostgreSQL with automatic, zero-configuration SQLite fallback (`sqlite:///./sql_app.db`) for isolated, offline local development. Exposes a reusable `get_db()` dependency generator.

### 3.2 Ingestion Engine (`services/ingestion.py`) — Milestone M2 (Verified)
- **Pydantic v2 Schema Enforcement**: `RawTransactionRow` validates all incoming transaction rows for type safety:
  - `timestamp`: String format validated and parsed to timezone-aware UTC datetime.
  - `src_ip`, `dst_ip`: String IP addresses.
  - `src_port`, `dst_port`: Integer port allocations.
  - `txid`: String transaction hash.
  - `input_addresses`, `output_addresses`: Typed lists of string wallet addresses.
  - `input_amounts`, `output_amounts`: Typed lists of float values.
  - `fee`: Optional float default `0.0`.
  - `script_type`: Optional string default `"p2pkh"`.
- **Multi-Format Ingestion**:
  - Handles JSON arrays containing structured lists.
  - Handles CSV files containing stringified JSON lists (`json.loads` normalization).
- **Cached MaxMind GeoIP Enrichment**:
  - Offline lookup against `data/geolite2/GeoLite2-City.mmdb`.
  - In-memory `GEOIP_CACHE` avoids redundant disk reads for recurrent IP addresses.
  - Graceful fallback to `"UNKNOWN"` country code when database file is missing or IP is private/loopback.
- **Robust Error Handling**: Drops malformed rows with warning logs; raises `ValueError` if zero valid records exist.

### 3.3 Scoring Service Stub (`services/scoring.py`) — Milestone M3 Foundation
- Defines Pydantic schema `AlertData`:
  - `entity_type`: `"wallet"` or `"ip"`
  - `entity_id`: Identifier string
  - `risk_score`: 0.0 to 100.0 float
  - `confidence`: 0.0 to 1.0 float
  - `reason`: Descriptive explanation
  - `shap_explanation`: Dictionary of normalized feature contributions
- Exposes `score_entities(df: pd.DataFrame) -> List[AlertData]` contract stub.

### 3.4 REST API Endpoints (`routers/`)
- `/api/v1/ingest`: Receives multipart file uploads, validates extension (`.csv`, `.json`), stores file to disk, runs `process_raw_file()`, and returns record/alert counts.
- `/api/v1/alerts`: Returns `PaginatedAlertResponse` with client filtering on `min_score` and `entity_type`.
- `/api/v1/dashboard/stats`: Aggregates active peer counts, total transactions, high/medium alert counts, risk score histogram bins, and top flagged countries.
- `/api/v1/graph`: Returns typed `CytoscapeGraphResponse` containing `NodeData` and `EdgeData` with optional entity focus and hop depth (1–3).
- `/api/v1/search`: Parses search query and detects entity format (IP address regex, Bitcoin address heuristics, or 64-character hex txid).

---

## 4. Interface Contracts & Status

| Contract | Function Signature | Input | Output | Status |
|---|---|---|---|---|
| **Contract 1 (M2)** | `process_raw_file(filepath: str)` | Raw CSV or JSON filepath | Clean pandas DataFrame (14 columns) | **VERIFIED & TESTED** |
| **Contract 2 (M3)** | `score_entities(df: pd.DataFrame)` | Ingested DataFrame | `List[AlertData]` | Stub implemented; pending real ML integration |

---

## 5. Immediate Next Steps
1. Connect `routers/ingest.py` and `routers/alerts.py` to persistent database tables (SQLAlchemy models for transactions, entities, and alerts).
2. Wire real ML inference pipeline (`ml/feature_engineering.py` + `ml/model.py`) into `services/scoring.py`.
3. Add unit tests for FastAPI routers using `httpx.AsyncClient` / `TestClient`.
