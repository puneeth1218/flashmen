from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.services.database import get_db, Alert

router = APIRouter(prefix="/api/v1", tags=["Alerts"])

@router.get("/alerts")
def get_alerts(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns a list of risk alerts retrieved from the database, sorted by risk_score descending.
    """
    alerts_query = db.query(Alert).order_by(desc(Alert.risk_score)).offset(skip).limit(limit).all()
    
    result = []
    for a in alerts_query:
        result.append({
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "risk_score": a.risk_score,
            "confidence": a.confidence,
            "reason": a.reason,
            "shap_explanation": {"dummy_feature": 0.5} # Satisfy the frontend AlertTable modal requirements
        })
    return result
