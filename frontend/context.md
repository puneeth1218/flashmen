# Frontend Module Context & Implementation Status

> **Module**: `frontend/`  
> **Status**: Full SPA Scaffolding Complete · Aceternity Dark UI Implemented  
> **Framework**: React 18 · TypeScript · Vite · Tailwind CSS · React Query · Axios

---

## 1. Module Overview & Role
The `frontend/` module provides a highly-responsive, premium dark-mode web application for intelligence analysts using the **Bitcoin Traffic Monitor (Flashmen)**. The UI has been heavily refined to follow the **Aceternity UI / Maciej Zadykowicz** design system, focusing on:
- High-contrast typography (pure white text on deep black canvases).
- Minimalist geometric surfaces (`zinc-950` cards with 1px hairlines).
- "Ghost pill" badges and pure-white primary CTA buttons.
- Real-time forensic alerts and file ingestion drag-and-drop zones.

---

## 2. Directory Structure & File Contents

```text
frontend/
├── tailwind.config.js        # Strict Aceternity Dark palette (paper, canvas, ink, hairline, electric-blue)
├── src/
│   ├── App.tsx               # Root component with React Router v6 & global dark canvas wrapper
│   ├── index.css             # Tailwind base layer overriding global body to pure deep black (#000000)
│   ├── services/
│   │   └── api.ts            # Axios clients and React Query mutation endpoints
│   ├── components/
│   │   ├── Navbar.tsx        # Aceternity-style sticky frosted header (44px/60px, no heavy borders)
│   │   ├── AlertTable.tsx    # High-contrast borderless table for triage
│   │   ├── FileUpload.tsx    # Sleek drag-and-drop dropzone with white-pill CTA
│   │   └── ui/               # Reusable primitive system
│   │       ├── Card.tsx      # Core surface (rounded-12px, border-hairline, bg-paper)
│   │       ├── Badge.tsx     # Apple/Aceternity ghost-pill badges for risk scores
│   │       └── Skeleton.tsx  # Loading state indicators (animate-pulse)
│   └── pages/
│       ├── DashboardPage.tsx # Route /: Full-bleed transparent sections floating over global grid/dark canvas
│       ├── GraphPage.tsx     # Route /graph: (Pending visual overhaul integration)
│       └── UploadPage.tsx    # Route /upload: Aceternity dark ingestion UI
```

---

## 3. What Has Been Implemented By This Point

### 3.1 Design System Pivot (Aceternity Dark Mode)
- Completely overhauled the UI from the original muddy slate/amber to a pure high-contrast dark mode.
- **Colors**: Defined semantic tokens `paper` (#09090b), `canvas` (#000000), `ink` (#ffffff), `hairline` (#27272a), and `electric-blue` (#ffffff).
- **Typography**: Stripped out excessive monospace fonts; implemented crisp tracking (`tracking-apple-body`, `tracking-apple-heading`) using `Inter`.
- **Components**: 
  - `Card`: Flattened all drop-shadows, set 12px radii, added crisp 1px zinc-800 borders.
  - `Badge`: Removed background fills, converted to lightweight "ghost pills" (`bg-transparent`, thin borders).
  - `Button`: Standardized primary CTAs (like "Ingest Logs") to solid white pills with black text (`bg-white text-black rounded-full`).

### 3.2 Data Mutations & Ingestion (`src/components/FileUpload.tsx`)
- Integrated `@tanstack/react-query` `useMutation` for robust file uploading.
- Support for `.csv`, `.json`, and `.jsonl` PCAP/Telemetry dumps.
- Sleek drag-and-drop handling with hover-state border transitions (`border-white/50`).
- Success states returning inline alerts containing processed records and flagged entities.

### 3.3 Alert Triage (`src/components/AlertTable.tsx`)
- Minimalist data presentation without heavy table cell boundaries.
- Rows highlight faintly on hover (`hover:bg-canvas`).
- Inline risk badges calculate dynamic text/border colors based on standard numeric thresholds (e.g. `risk_score > 90`).

---

## 4. Immediate Next Steps
1. **Graph UI Alignment**: Ensure the Cytoscape graph canvas in `GraphPage.tsx` integrates smoothly with the new deep black `#000000` canvas (adjust node colors to pop against pure black).
2. **WebSockets**: Introduce live-polling or true WebSocket connections to automatically append alerts to the `AlertTable` without requiring an explicit React Query invalidation trigger.
3. **Expandable Rows**: Wire up the "Details `>`" button in the `AlertTable` to slide down or open a sheet displaying SHAP explainability matrices for the anomaly.
