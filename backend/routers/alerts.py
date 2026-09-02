"""
Alerts Router: GET /api/v1/alerts
Provides paginated list of suspicious entity alerts with risk scoring & SHAP breakdowns.
"""

from typing import List, Optional, Literal
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from backend.services.scoring import AlertData

router = APIRouter(prefix="/api/v1", tags=["Alerts"])


class PaginatedAlertResponse(BaseModel):
    total: int = Field(..., description="Total count of alerts matching criteria")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of alerts per page")
    alerts: List[AlertData] = Field(..., description="List of alert items")


# Static mock alert data for clean scaffolding functionality
MOCK_ALERTS: List[AlertData] = [
    AlertData(
        entity_type="ip",
        entity_id="198.51.100.45",
        risk_score=94.2,
        confidence=0.96,
        reason="Rapid connection fan-out across 120+ peer nodes in <10s",
        shap_explanation={"fan_out_degree": 0.62, "tx_rate": 0.25, "geo_shift": 0.09}
    ),
    AlertData(
        entity_type="wallet",
        entity_id="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        risk_score=88.7,
        confidence=0.91,
        reason="Peel-chain structure matching known mixer exit signatures",
        shap_explanation={"peel_chain_depth": 0.54, "equal_output_ratio": 0.31, "decay_time": 0.06}
    ),
    AlertData(
        entity_type="ip",
        entity_id="203.0.113.89",
        risk_score=72.0,
        confidence=0.84,
        reason="Repeated non-standard P2P port scanning",
        shap_explanation={"port_entropy": 0.48, "failed_handshakes": 0.26}
    ),
    AlertData(
        entity_type="wallet",
        entity_id="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        risk_score=65.4,
        confidence=0.79,
        reason="CoinJoin round participation with high output fan-in",
        shap_explanation={"coinjoin_similarity": 0.42, "round_frequency": 0.23}
    ),
]


@router.get("/alerts", response_model=PaginatedAlertResponse)
async def get_alerts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum risk score threshold"),
    entity_type: Optional[Literal["wallet", "ip"]] = Query(None, description="Filter by entity type")
) -> PaginatedAlertResponse:
    """
    Returns a paginated list of risk alerts filtered by minimum score and entity type.
    """
    filtered = [
        a for a in MOCK_ALERTS
        if a.risk_score >= min_score and (entity_type is None or a.entity_type == entity_type)
    ]

    total = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = filtered[start_idx:end_idx]

    return PaginatedAlertResponse(
        total=total,
        page=page,
        limit=limit,
        alerts=paginated_items
    )
