from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.services.database import get_db, Alert

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retrieves global dashboard aggregates by querying the Alert table.
    """
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    critical_alerts = db.query(func.count(Alert.id)).filter(Alert.risk_score >= 75).scalar() or 0
    latest_update = db.query(func.max(Alert.created_at)).scalar()
    
    dist_0_25 = db.query(func.count(Alert.id)).filter(Alert.risk_score <= 25).scalar() or 0
    dist_26_50 = db.query(func.count(Alert.id)).filter(Alert.risk_score > 25, Alert.risk_score <= 50).scalar() or 0
    dist_51_75 = db.query(func.count(Alert.id)).filter(Alert.risk_score > 50, Alert.risk_score < 75).scalar() or 0
    
    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "latest_update": latest_update.isoformat() if latest_update else None,
        "risk_score_distribution": {
            "0-25": dist_0_25,
            "26-50": dist_26_50,
            "51-75": dist_51_75,
            "76-100": critical_alerts
        }
    }
