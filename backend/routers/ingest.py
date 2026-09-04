"""
Ingestion Router: POST /api/v1/ingest
Handles file upload of raw Bitcoin traffic logs and triggers ingestion + scoring pipeline.
"""

import os
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.services.ingestion import process_raw_file
from backend.services.scoring import score_entities
from backend.services.database import get_db, Alert

router = APIRouter(prefix="/api/v1", tags=["Ingest"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/synthetic")


@router.post("/ingest", status_code=202)
async def ingest_traffic_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Accepts raw CSV/JSON Bitcoin traffic log file upload, runs parsing pipeline,
    scores entities, and inserts alerts into the database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    # 1. Save uploaded file temporarily
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # 2. Process, Score, and Store
    try:
        df = process_raw_file(file_location)
        scored_alerts = score_entities(df)
        
        alert_models = []
        for alert_data in scored_alerts:
            alert_model = Alert(
                entity_type=alert_data.entity_type,
                entity_id=alert_data.entity_id,
                risk_score=alert_data.risk_score,
                confidence=alert_data.confidence,
                reason=alert_data.reason
            )
            alert_models.append(alert_model)
        
        # 3. Bulk insert and commit
        if alert_models:
            db.add_all(alert_models)
            db.commit()
            
        return {
            "status": "success",
            "filename": file.filename,
            "processed_records": len(df),
            "generated_alerts_count": len(scored_alerts),
            "message": f"Successfully ingested {len(df)} records and flagged {len(scored_alerts)} suspicious entities."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process ingestion file: {str(e)}"
        )
