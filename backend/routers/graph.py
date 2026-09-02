"""
Graph Router: GET /api/v1/graph
Exposes Cytoscape-compliant JSON network graph structure for frontend visualization.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["Graph"])


class NodeData(BaseModel):
    id: str
    label: str
    type: str  # 'wallet', 'ip', 'tx'
    risk_score: float = 0.0


class NodeItem(BaseModel):
    data: NodeData


class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    amount: float = 0.0
    label: str = ""


class EdgeItem(BaseModel):
    data: EdgeData


class CytoscapeGraphResponse(BaseModel):
    nodes: List[NodeItem]
    edges: List[EdgeItem]


@router.get("/graph", response_model=CytoscapeGraphResponse)
async def get_network_graph(
    entity_id: Optional[str] = Query(None, description="Optional entity ID to focus graph traversal around"),
    depth: int = Query(2, ge=1, le=5, description="Graph expansion depth level")
) -> CytoscapeGraphResponse:
    """
    Returns Cytoscape-formatted JSON containing graph nodes (IPs, Wallets) and edges (Transactions, P2P Traffic).
    Contract 3 (M4 -> M5).
    """
    # Static stub graph matching Cytoscape JSON specification
    nodes = [
        NodeItem(data=NodeData(id="198.51.100.45", label="IP: 198.51.100.45", type="ip", risk_score=94.2)),
        NodeItem(data=NodeData(id="203.0.113.89", label="IP: 203.0.113.89", type="ip", risk_score=72.0)),
        NodeItem(data=NodeData(id="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", label="Wallet: 1A1zP...", type="wallet", risk_score=88.7)),
        NodeItem(data=NodeData(id="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", label="Wallet: bc1qxy...", type="wallet", risk_score=65.4)),
        NodeItem(data=NodeData(id="tx_11029384", label="Tx: 11029384", type="tx", risk_score=0.0)),
    ]

    edges = [
        EdgeItem(data=EdgeData(id="e1", source="198.51.100.45", target="tx_11029384", amount=2.5, label="P2P Broadcast")),
        EdgeItem(data=EdgeData(id="e2", source="tx_11029384", target="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", amount=2.5, label="Output")),
        EdgeItem(data=EdgeData(id="e3", source="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", target="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", amount=1.2, label="Peel Chain Tx")),
        EdgeItem(data=EdgeData(id="e4", source="203.0.113.89", target="198.51.100.45", amount=0.0, label="Handshake")),
    ]

    return CytoscapeGraphResponse(nodes=nodes, edges=edges)
