# Frontend Module Context & Implementation Status

> **Module**: `frontend/`  
> **Status**: Full SPA Scaffolding Complete · Component Suite Operational  
> **Framework**: React 18 · TypeScript · Vite · Tailwind CSS · Cytoscape.js · Axios  

---

## 1. Module Overview & Role
The `frontend/` module provides a responsive web application for intelligence analysts and investigators using the **Bitcoin Traffic Monitor (Flashmen)**. It visualizes:
- Real-time forensic alerts with expandable SHAP explainability breakdowns.
- Network telemetry metrics (transactions ingested, peer counts, risk distributions).
- Interactive topological investigation graphs rendered via Cytoscape.js.
- Offline data upload workflows for raw CSV/JSON transaction dumps.

---

## 2. Directory Structure & File Contents

```
frontend/
├── Dockerfile                # Multi-stage production container with Nginx 1.25 alpine
├── nginx.conf                # Nginx reverse proxy routing /api requests to backend:8000
├── package.json              # NPM manifest (React 18, Vite, Tailwind, Cytoscape, Lucide)
├── tsconfig.json             # TypeScript strict configuration
├── vite.config.ts            # Vite dev server setup (port 3000, /api proxy to localhost:8000)
└── src/
    ├── App.tsx               # Root component with React Router v6 navigation
    ├── main.tsx              # Application bootstrap & DOM root mount
    ├── index.css             # Tailwind directives and global typography styles
    ├── services/
    │   └── api.ts            # Strongly-typed Axios client mirroring all backend Pydantic models
    ├── components/
    │   ├── Navbar.tsx        # Top navigation with global entity search input & route links
    │   ├── StatsSummary.tsx  # 4-card metric grid (Transactions, High Risk, Entities, Peers)
    │   ├── AlertTable.tsx    # Sortable triage table with expandable SHAP feature attribution
    │   └── GraphViewer.tsx   # Cytoscape.js canvas with COSE layout, node badges & legends
    └── pages/
        ├── DashboardPage.tsx # Route /: Telemetry metrics & interactive alert triage
        ├── GraphPage.tsx     # Route /graph: Topological graph explorer with hop depth selector
        └── UploadPage.tsx    # Route /upload: Drag-and-drop file ingestion interface
```

---

## 3. What Has Been Implemented By This Point

### 3.1 Typed API Integration Layer (`src/services/api.ts`)
- Configured Axios instance with dynamic `VITE_API_BASE_URL` resolution (defaults to `http://localhost:8000`).
- Strict TypeScript interface contracts matching backend models:
  - `AlertData`: Type, identifier, risk score, confidence, reason, and `shap_explanation` map.
  - `PaginatedAlertResponse`: Paginated array with total counts.
  - `DashboardStats`: Counter aggregates, histogram distributions, and country rankings.
  - `CytoscapeGraphResponse`: Standard Cytoscape nodes and edges.
  - `IngestResponse`: Upload acknowledgement and processed row metrics.
  - `SearchResponse`: Polymorphic search query results.
- Exported API operations: `fetchAlerts()`, `fetchDashboardStats()`, `fetchNetworkGraph()`, `uploadTrafficFile()`, and `globalSearch()`.

### 3.2 UI Components (`src/components/`)
- **`Navbar.tsx`**:
  - Global entity search bar triggering navigation to `/graph?focus={query}`.
  - Navigation tabs with active route highlighting (Dashboard, Graph Explorer, Ingest Logs).
- **`StatsSummary.tsx`**:
  - Color-coded metric cards with Lucide icons (Total Transactions, High Risk Alerts, Monitored Entities, Active Peers).
- **`AlertTable.tsx`**:
  - Color-graded risk badges: High (≥75, Red), Medium (≥40, Amber), Low (<40, Green).
  - Entity category chips (Purple = Wallet, Blue = IP).
  - Expandable row accordion rendering granular SHAP feature attribution bars.
- **`GraphViewer.tsx`**:
  - Canvas integration using `cytoscape` and `react-cytoscapejs`.
  - Visual distinction: IP nodes (green ellipses), Wallet nodes (purple rectangles), Transaction nodes (hexagons), and High Risk nodes (prominent red borders).
  - Dynamic COSE physics layout with directed arrows and node selection inspector.

### 3.3 Application Pages (`src/pages/`)
- **`DashboardPage.tsx`**: Orchestrates `StatsSummary` cards and the paginated `AlertTable`.
- **`GraphPage.tsx`**: Graph investigation workspace with search query parameter binding and hop depth controls (1, 2, or 3 hops).
- **`UploadPage.tsx`**: File ingestion interface with drag-and-drop support, format validation (`.csv`, `.json`), upload progress feedback, and error handling.

---

## 4. Immediate Next Steps
1. Add live polling or WebSocket listener on `DashboardPage.tsx` to refresh telemetry as new files are uploaded.
2. Implement node click callbacks in `GraphViewer.tsx` to display lateral entity inspection drawers.
3. Add client-side CSV export for filtered alert lists in `AlertTable.tsx`.
