import json
import re
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.services.database import get_db, Alert

router = APIRouter(prefix="/api/v1", tags=["Alerts"])


def _clean_id(raw_id: str) -> str:
    if not raw_id:
        return ""
    s = str(raw_id).strip()
    return re.sub(r"^[\[\(\{\'\"]+|[\]\)\}\'\"]+$", "", s).strip()


@router.get("/alerts")
def get_alerts(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns a list of risk alerts retrieved from the database, sorted by risk_score descending,
    deduplicated by entity (keeping the highest risk / most recent alert per entity).
    """
    alerts_query = db.query(Alert).order_by(desc(Alert.risk_score), desc(Alert.created_at)).limit(max(limit * 20, 1000)).all()
    
    unique_alerts = []
    seen = set()
    for a in alerts_query:
        clean_id = _clean_id(a.entity_id)
        if not clean_id:
            continue
        key = (clean_id, a.entity_type)
        if key in seen:
            continue
        seen.add(key)

        clean_reason = re.sub(r"^flagged due to:\s*", "", a.reason or "", flags=re.IGNORECASE).strip()
        if not clean_reason:
            clean_reason = "Anomalous Bitcoin network pattern detected"

        shap_exp = a.shap_explanation
        if isinstance(shap_exp, str):
            try:
                shap_exp = json.loads(shap_exp)
            except Exception:
                shap_exp = {}
        elif not isinstance(shap_exp, dict):
            shap_exp = {}

        unique_alerts.append({
            "entity_type": a.entity_type,
            "entity_id": clean_id,
            "risk_score": round(float(a.risk_score), 1) if a.risk_score is not None else 0.0,
            "confidence": round(float(a.confidence), 2) if a.confidence is not None else 0.0,
            "reason": clean_reason,
            "shap_explanation": shap_exp
        })
        if len(unique_alerts) >= skip + limit:
            break

    return unique_alerts[skip : skip + limit]


@router.post("/alerts/clear")
@router.delete("/alerts")
@router.post("/clear")
def clear_alerts(db: Session = Depends(get_db)):
    """
    Clears all stored alerts and logs from the database, resetting the monitor state.
    """
    count = db.query(Alert).delete()
    db.commit()
    return {
        "status": "success",
        "message": f"Successfully cleared {count} alerts and logs.",
        "cleared_count": count
    }
