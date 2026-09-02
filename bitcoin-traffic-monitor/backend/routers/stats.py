"""
Stats Router: GET /api/v1/dashboard/stats
Summary metrics and health statistics for the traffic monitoring dashboard.
"""

from typing import Dict, Any, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


class DashboardStatsResponse(BaseModel):
    total_transactions_ingested: int = Field(..., description="Total count of transactions processed")
    total_entities_monitored: int = Field(..., description="Active unique IP addresses and wallets monitored")
    high_risk_alerts_count: int = Field(..., description="Alerts with risk score >= 75")
    medium_risk_alerts_count: int = Field(..., description="Alerts with risk score between 40 and 74")
    active_peers_count: int = Field(..., description="Currently active P2P node connections")
    risk_score_distribution: Dict[str, int] = Field(..., description="Histogram of risk score buckets")
    top_flagged_countries: List[Dict[str, Any]] = Field(..., description="Geographical distribution of suspicious IPs")


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats() -> DashboardStatsResponse:
    """
    Retrieves global network traffic metrics, alert statistics, and system health status.
    """
    return DashboardStatsResponse(
        total_transactions_ingested=142850,
        total_entities_monitored=12400,
        high_risk_alerts_count=38,
        medium_risk_alerts_count=142,
        active_peers_count=850,
        risk_score_distribution={
            "0-25": 10500,
            "26-50": 1400,
            "51-75": 142,
            "76-100": 38
        },
        top_flagged_countries=[
            {"country": "US", "flagged_count": 18},
            {"country": "RU", "flagged_count": 12},
            {"country": "CN", "flagged_count": 5},
            {"country": "DE", "flagged_count": 3}
        ]
    )
