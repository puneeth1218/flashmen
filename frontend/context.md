# Frontend Module Context & Implementation Status

> **Module**: `frontend/`  
> **Status**: Fully Operational · Aceternity Dark UI · Global Search, Engine Health & Graph Navigation Active  
> **Framework**: React 18 · TypeScript · Vite · Tailwind CSS · React Query · Axios · Cytoscape.js  

---

## 1. Module Overview & Role
The `frontend/` module provides a high-contrast, dark-mode analytical application for cyber intelligence and Bitcoin network forensics. The UI is designed under the **Aceternity UI** design system:
- High-contrast typography (crisp white on deep black canvases `#000000`).
- Minimalist geometric surfaces (`zinc-950` cards with 1px zinc-800 borders).
- "Ghost pill" badges and pure-white primary CTA buttons.
- Real-time forensic alerts with SHAP feature attribution inspection drawers.
- Interactive Cytoscape.js topological graph explorer with dynamic ego-depth traversal.
- Global search bar (`⌘K` / `/`) and live backend engine health indicator.

---

## 2. Directory Structure & File Contents

```text
frontend/
├── package.json              # React 18, Vite, Tailwind, Cytoscape, Lucide React, Axios, React Query
├── vite.config.ts            # Dev server config (proxying /api to http://localhost:8000)
├── tailwind.config.js        # Strict Aceternity Dark palette (paper, canvas, ink, hairline)
└── src/
    ├── App.tsx               # Root component with React Router v6 & persistent query state
    ├── index.css             # Tailwind base layer overriding global body to pure deep black (#000000)
    ├── services/
    │   └── api.ts            # Typed Axios client & query functions (alerts, stats, graph, ingest, search)
    ├── components/
    │   ├── Navbar.tsx        # Sticky frosted header with global search (⌘K) & live engine health badge
    │   ├── AlertTable.tsx    # Forensic triage table with SHAP attribution inspection drawer & graph links
    │   ├── FileUpload.tsx    # Drag-and-drop CSV/JSON upload zone with inline success/error badges
    │   ├── StatsSummary.tsx  # Telemetry summary grid (Transactions, Volume, Peers, Alerts)
    │   ├── RiskDistributionChart.tsx # SVG risk score distribution histogram
    │   ├── graph/
    │   │   ├── GraphViewer.tsx       # Cytoscape.js canvas with COSE layout & node styling
    │   │   ├── NodeDetailPanel.tsx   # Slide-over inspector for selected node attributes & edges
    │   │   └── GraphViewer.css       # Canvas styling
    │   └── ui/                       # Design system primitives (Card, Badge, Skeleton)
    └── pages/
        ├── DashboardPage.tsx # Route /: StatsSummary, RiskDistributionChart, and AlertTable
        ├── GraphPage.tsx     # Route /graph: Topological graph explorer with ego-depth filter (1–3 hops)
        └── UploadPage.tsx    # Route /upload: Drag-and-drop file ingestion zone
```

---

## 3. What Has Been Implemented

### 3.1 Design System (Aceternity Dark Mode)
- **Palette**: `canvas` (`#000000`), `paper` (`#09090b`), `hairline` (`#27272a`), `ink` (`#ffffff`).
- **Typography**: Apple-style tracking (`tracking-apple-body`, `tracking-apple-heading`) with `Inter`.
- **Primitives**: Crisp 1px border cards, ghost-pill badges for risk levels (red ≥80, amber ≥60, green <60).

### 3.2 Global Navbar Search & Live Engine Health (`src/components/Navbar.tsx`)
- **Global Search**:
  - Accessible via `⌘K`, `Ctrl+K`, or pressing `/`.
  - Auto-queries `GET /api/v1/search?q=<query>` with debouncing.
  - Displays instant dropdown previews for matching entities with risk badges and reason previews.
  - Direct selection navigates immediately to `/graph?entity=<entity_id>&depth=1`.
- **Core Engine Active Indicator**:
  - Polls backend root `GET /` every 30 seconds via `healthCheck()`.
  - Displays green pulsing dot when backend is active; amber badge when offline.

### 3.3 Risk Distribution Chart (`src/components/RiskDistributionChart.tsx`)
- Mounted directly onto `DashboardPage.tsx`.
- Visualizes risk score distribution across 5 buckets (0-20, 21-40, 41-60, 61-80, 81-100).
- Displays color-graded vertical bars with hover count tooltips and percentage breakdowns.

### 3.4 Forensic Alert Triage & SHAP Drawer (`src/components/AlertTable.tsx`)
- High-contrast data presentation with sortable columns and entity type badges (`wallet` / `ip`).
- **Persistent Data**: No data loss on page refresh (removed legacy `clearAlerts()` and `beforeunload` wipes).
- **SHAP Feature Attribution**: Clicking a row opens a slide-out drawer rendering the normalized feature attribution percentages (`shap_explanation`) saved in the database.
- **Cross-Page Navigation**: Direct link in each row to inspect the entity's ego-network on `/graph?entity=<id>&depth=1`.

### 3.5 Network Topology Explorer (`src/pages/GraphPage.tsx` & `src/components/graph/`)
- Cytoscape.js canvas with COSE layout, styled nodes (wallets, IPs, transactions), and directed transfer edges.
- Depth selector allows dynamically expanding ego-networks from 1 to 3 hops.
- Inspecting a node displays address, entity type, observed balance, and connected edges.

---

## 4. Setup & Running Instructions

### Development Server:
```bash
cd frontend
npm install
npm run dev
```
- Local dev server: [http://localhost:5173](http://localhost:5173)
- Automatically proxies API requests to `http://localhost:8000`.

### Production Build:
```bash
cd frontend
npm run build
```
- Output compiled to `frontend/dist/`.

### Air-Gapped Offline Installation:
```bash
cd frontend
npm ci --cache ../offline_packages/npm --prefer-offline
```

