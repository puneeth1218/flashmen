"""
Graph Router: GET /api/v1/graph
Exposes Cytoscape-compliant JSON network graph structure for frontend visualization.
"""

import os
import glob
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from backend.services.ingestion import process_raw_file
from graph.builder import build_cytoscape_graph

router = APIRouter(prefix="/api/v1", tags=["Graph"])


class NodeData(BaseModel):
    id: str
    label: str
    type: str  # 'wallet', 'ip', 'tx'
    risk_score: float = 0.0
    pattern_tag: Optional[str] = ""


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
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/synthetic")
    
    if not os.path.exists(UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="Upload directory not found. No data available.")
        
    files = glob.glob(os.path.join(UPLOAD_DIR, "*"))
    files = [f for f in files if f.endswith(('.csv', '.json'))]
    if not files:
        raise HTTPException(status_code=404, detail="No ingested traffic files found.")
        
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        df = process_raw_file(latest_file)
        graph_data = build_cytoscape_graph(df, entity_id=entity_id, depth=depth)
        return CytoscapeGraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate graph: {str(e)}")
