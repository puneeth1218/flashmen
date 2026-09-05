# Graph Analytics Module Context & Implementation Status

> **Module**: `graph/`  
> **Status**: Operational · Dynamic Ego-Graph Traversal Verified · Cytoscape.js Serialization Operational  
> **Core Stack**: NetworkX · pandas · Cytoscape.js JSON Schema  

---

## 1. Module Overview & Role
The `graph/` module constructs, analyzes, and serializes the dual-layer network and transaction topology for the **Bitcoin Traffic Monitor** platform. It bridges:
- **Network-Layer P2P Observations**: IP nodes communicating via Bitcoin gossip protocol edges (`P2P Traffic`).
- **Ledger-Layer Blockchain Flows**: Wallet address nodes, intermediate transaction hash vertices, and input/output value transfer edges.
- **Dynamic Ego-Network Traversal**: Localized subgraph extraction around a suspicious entity (1 to 3 hops) using NetworkX.
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

## 3. What Has Been Implemented

### 3.1 NetworkX Graph Construction (`builder.py`)
- **`NetworkGraphBuilder` Class**:
  - Encapsulates an internal directed graph (`nx.DiGraph()`).
  - `add_dataframe_records(df: pd.DataFrame)`:
    - **IP Nodes**: Adds `src_ip` and `dst_ip` nodes with `type="ip"`.
    - **P2P Edges**: Links `src_ip -> dst_ip` labeled `"P2P Traffic"` with associated transaction hash.
    - **Wallet Nodes & Flow Edges**: Parses comma-separated or list-based addresses. Creates wallet vertices (`type="wallet"`), intermediate transaction vertices (`type="tx"`), and directed edges (`in_wallet -> tx` labeled `"Input"`, `tx -> out_wallet` labeled `"Output"` with transfer amounts).
    - **Heuristic Pattern & Risk Mapping**: Automatically integrates detected patterns (`is_peel_chain`, `is_mixer`) and maps them to node `risk_score` (85.0 for peel chains, 90.0 for mixers) and `pattern_tag` (`"Peel Chain"`, `"Mixer"`).
- **Cytoscape.js Serialization (`to_cytoscape_json()`)**:
  - Implements **Contract 3 (M4 -> M5)**.
  - Outputs standard Cytoscape-compliant structure with `pattern_tag`:
    ```json
    {
      "nodes": [{"data": {"id": "...", "label": "...", "type": "ip|wallet|tx", "risk_score": 85.0, "pattern_tag": "Peel Chain"}}],
      "edges": [{"data": {"id": "...", "source": "...", "target": "...", "label": "...", "amount": 0.0}}]
    }
    ```
- **Functional Interface (`build_cytoscape_graph`)**:
  - **Overcrowding Resolution (Default Global View)**: When `entity_id` is omitted, rather than dumping 600+ nodes into an unreadable hairball, filters the graph to include top high-risk anomalous seed nodes (`risk_score >= 70.0` or `pattern_tag != ''`) and their immediate 1-hop connected neighbors, capping the view at 45 most relevant nodes.
  - **Ego Subgraph Extraction**: When `entity_id` is provided, performs `nx.ego_graph(G, n=target, radius=depth, undirected=True)` to inspect the localized multi-hop transaction neighborhood.

### 3.2 Dynamic Ego-Graph Traversal (`backend/routers/graph.py`)
- Integrated with `GET /api/v1/graph?entity_id=<id>&depth=<1..3>`:
  - Invokes `build_cytoscape_graph()` with entity and depth filtering.
  - Returns structured `CytoscapeGraphResponse` containing `NodeData` (with `pattern_tag`) and `EdgeData`.

### 3.3 On-Chain Heuristic Analyzers (`heuristics.py`)
- **Robust List / String Address Counting (`get_count`)**:
  - Addresses issue where ingested DataFrame address fields are Python `list` objects instead of comma-separated strings.
  - Evaluates lists, comma-separated strings, and scalar addresses cleanly, ensuring correct input/output counting for peel chain and mixer algorithms.
- **Peel-Chain Detection (`detect_peel_chains`)**:
  - Evaluates transactions following the classic 1-input, 2-output structure where one output serves as the payment recipient and the other represents change returned to the sender.
  - Flags peel chains in batch with `add_heuristic_columns()`.
- **CoinJoin / Mixer Detection (`detect_mixers`)**:
  - Analyzes transaction structure for multi-party anonymity pools (≥3 inputs and ≥3 outputs).
  - Flags mixing rounds with participant counts and confidence tags.

---

## 4. Setup & Running Instructions

Execute all commands from the **repository root (`flashmen/`)**:

```bash
# 1. Activate Python virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux:
source .venv/bin/activate

# 2. Test graph construction & serialization
python -c "import pandas as pd; from graph.builder import build_cytoscape_graph; df = pd.read_csv('data/synthetic/sample_traffic.csv'); g = build_cytoscape_graph(df); print('Nodes:', len(g['nodes']), 'Edges:', len(g['edges']))"
```

