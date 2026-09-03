# Graph Analytics Module Context & Implementation Status

> **Module**: `graph/`  
> **Status**: Contract 3 Verified (Milestone M4) · Topology Builder & Heuristics Operational  
> **Core Stack**: NetworkX · pandas · Cytoscape.js JSON Schema  

---

## 1. Module Overview & Role
The `graph/` module constructs, analyzes, and serializes the dual-layer network and transaction topology for the **Bitcoin Traffic Monitor** platform. It bridges:
- **Network-Layer P2P Observations**: IP nodes communicating via Bitcoin gossip protocol edges.
- **Ledger-Layer Blockchain Flows**: Wallet address nodes, transaction hash vertices, and input/output value transfer edges.
- **Forensic Heuristics**: Algorithmic detection of obfuscation strategies including rapid peel chains and CoinJoin/mixing pools.

---

## 2. Directory Structure & File Contents

```
graph/
├── __init__.py               # Package exports: build_cytoscape_graph, NetworkGraphBuilder, heuristics
├── builder.py                # Contract 3 (M4->M5): NetworkGraphBuilder & build_cytoscape_graph()
└── heuristics.py             # Domain-specific heuristics for peel chains and CoinJoin mixer detection
```

---

## 3. What Has Been Implemented By This Point

### 3.1 NetworkX Graph Construction (`builder.py`)
- **`NetworkGraphBuilder` Class**:
  - Encapsulates an internal directed graph (`nx.DiGraph()`).
  - `add_dataframe_records(df: pd.DataFrame)`:
    - **IP Nodes**: Adds `src_ip` and `dst_ip` nodes with `type="ip"`.
    - **P2P Edges**: Links `src_ip -> dst_ip` labeled `"P2P Traffic"` with associated transaction hash.
    - **Wallet Nodes & Flow Edges**: Parses comma-separated or list-based addresses. Creates wallet vertices (`type="wallet"`), intermediate transaction vertices (`type="tx"`), and directed edges (`in_wallet -> tx` labeled `"Input"`, `tx -> out_wallet` labeled `"Output"`).
- **Cytoscape.js Serialization (`to_cytoscape_json()`)**:
  - Implements **Contract 3 (M4 -> M5)**.
  - Outputs standard Cytoscape-compliant structure:
    ```json
    {
      "nodes": [{"data": {"id": "...", "label": "...", "type": "ip|wallet|tx"}}],
      "edges": [{"data": {"id": "...", "source": "...", "target": "...", "label": "..."}}]
    }
    ```
- **Functional Interface**: Exposes standalone `build_cytoscape_graph(df: pd.DataFrame) -> Dict` for zero-overhead service calls from FastAPI routers.

### 3.2 On-Chain Heuristic Analyzers (`heuristics.py`)
- **Peel-Chain Detection (`detect_peel_chains`)**:
  - Evaluates transactions following the classic 1-input, 2-output structure where one output serves as the payment recipient and the other represents change returned to the sender.
  - Returns descriptors with `txid`, `peel_source_wallet`, `recipient_wallet`, `change_wallet`, and initial confidence metrics.
- **CoinJoin / Mixer Detection (`detect_mixers`)**:
  - Analyzes transaction structure for multi-party anonymity pools (≥3 inputs and ≥3 outputs).
  - Flags mixing rounds with participant counts and confidence tags.

---

## 4. Interface Contracts & Status

| Contract | Function Signature | Input | Output | Status |
|---|---|---|---|---|
| **Contract 3 (M4→M5)** | `build_cytoscape_graph(df: pd.DataFrame)` | Ingested DataFrame | Cytoscape JSON `{nodes: [...], edges: [...]}` | **VERIFIED (240 nodes, 150 edges on sample)** |

---

## 5. Immediate Next Steps
1. Support multi-hop peel chain sequence tracing (following change addresses across consecutive blocks).
2. Integrate graph builder into `backend/routers/graph.py` with localized ego-network filtering (1 to 3 hops from target entity).
3. Annotate Cytoscape edges with transfer volume (`amount`) and risk scores (`risk_score`) for dynamic color coding in `frontend/src/components/GraphViewer.tsx`.
