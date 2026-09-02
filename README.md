# Bitcoin Traffic Monitor (`bitcoin-traffic-monitor`)

A complete monorepo for real-time Bitcoin network traffic analysis, anomaly detection, and graph visualization. Built with FastAPI, React (Vite + TypeScript), IsolationForest ML, SHAP explainability, and NetworkX graph analytics.

---

## 📁 Repository Structure

```
bitcoin-traffic-monitor/
├── docker-compose.yml        # Orchestrates PostgreSQL, FastAPI backend, React frontend
├── README.md                 # Project setup and offline instructions
├── .env.example              # Environment configuration template
├── .github/
│   ├── CODEOWNERS            # Workstream ownership assignments
│   └── workflows/ci.yml      # CI workflow for linting & tests
├── offline_packages/         # Directory for cached pip wheels and npm packages
├── data/
│   ├── geolite2/             # Location for GeoLite2-City.mmdb database
│   └── synthetic/            # Generated synthetic test datasets (CSV/JSON)
├── backend/                  # FastAPI web server and database operations
│   ├── main.py               # FastAPI entry point with CORS and lifespan handler
│   ├── database.py           # SQLAlchemy setup (Postgres/SQLite fallback)
│   ├── routers/              # API route controllers (ingest, alerts, stats, graph, search)
│   └── services/             # Core business logic (ingestion & scoring contracts)
├── ml/                       # Machine Learning models and feature pipelines
│   ├── feature_engineering.py# Feature aggregation pipeline for IPs and Wallets
│   ├── model.py              # IsolationForest anomaly detection model wrapper
│   ├── explainer.py          # SHAP TreeExplainer wrapper for model interpretability
│   ├── dataset_gen.py        # Faker-based synthetic Bitcoin traffic generator
│   └── tests/                # Unit test suite for ML pipelines
├── graph/                    # Graph analytics module
│   ├── builder.py            # NetworkX graph builder producing Cytoscape-formatted JSON
│   └── heuristics.py         # Heuristic rules (Peel-chain, CoinJoin/Mixer detection)
└── frontend/                 # React (Vite + TypeScript) user interface
    ├── package.json          # Dependency specifications (React Flow, Cytoscape, Axios)
    └── src/
        ├── components/       # Reusable visual components (AlertTable, GraphViewer, etc.)
        ├── pages/            # View pages (Upload, Dashboard, Graph)
        └── services/         # Axios API client bindings
```

---

## ⚙️ Quick Start

### 1. Environment Setup
Copy the example environment configuration:
```bash
cp .env.example .env
```

### 2. GeoLite2 Setup
Place your downloaded `GeoLite2-City.mmdb` database file into:
```
data/geolite2/GeoLite2-City.mmdb
```

### 3. Running with Docker Compose
Start all services (PostgreSQL, Backend API, Frontend UI):
```bash
docker-compose up --build
```
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)

---

## 🛠️ Local Manual Setup

### Backend & ML Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run synthetic dataset generator
python -m ml.dataset_gen --output ../data/synthetic/sample_traffic.csv

# Start FastAPI dev server
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📦 Offline Package Installation Instructions

If working in an offline/restricted network environment:

1. **Caching Python Wheels**:
   On a connected machine:
   ```bash
   pip wheel -r backend/requirements.txt -w offline_packages/pip_wheels/
   ```
   On the target offline machine:
   ```bash
   pip install --no-index --find-links=offline_packages/pip_wheels/ -r backend/requirements.txt
   ```

2. **Caching NPM Packages**:
   On a connected machine:
   ```bash
   cd frontend && npm pack
   # Or create tarball of node_modules / cache
   ```
   On the target offline machine:
   ```bash
   npm install --offline
   ```

---

## 👥 Team Workstreams & Responsibilities

| Role | Area | Core Files |
|------|------|------------|
| Team Lead / DevOps | Infra & CI | `docker-compose.yml`, `.github/` |
| Backend Eng 1 | API & Ingest | `backend/routers/ingest.py`, `backend/services/ingestion.py` |
| Backend Eng 2 | Database & Routers | `backend/database.py`, `backend/routers/alerts.py`, `stats.py`, `search.py` |
| ML Engineer 1 | Feature & Model | `ml/feature_engineering.py`, `ml/model.py`, `ml/dataset_gen.py` |
| ML Engineer 2 | SHAP & Scoring | `ml/explainer.py`, `backend/services/scoring.py` |
| Graph/Frontend Eng | Graph & UI | `graph/builder.py`, `graph/heuristics.py`, `frontend/` |
