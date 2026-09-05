"""
Ingestion Router: POST /api/v1/ingest
Handles file upload of raw Bitcoin traffic logs and triggers ingestion + scoring pipeline.
"""

import io
import json
import os
import re
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
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

    # 1. Read raw file bytes from UploadFile
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith(".json"):
            try:
                data = json.loads(contents.decode("utf-8"))
            except Exception:
                # Fallback for newline-delimited JSON (JSONL)
                data = pd.read_json(io.BytesIO(contents), lines=True)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # In case records are nested under a key like 'data' or 'transactions'
                records = data.get("transactions", data.get("data", [data]))
                df = pd.DataFrame(records)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                df = pd.DataFrame([data])
        else:
            # Auto-detect format fallback
            try:
                df = pd.read_csv(io.BytesIO(contents))
            except Exception:
                df = pd.read_json(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse upload file into DataFrame: {str(e)}"
        )

    # Persist uploaded file to disk (for graph visualizer and audit)
    try:
        with open(file_location, "wb") as buffer:
            buffer.write(contents)
    except Exception:
        pass

    # 2. Process, Score, and Store
    try:
        df = process_raw_file(df)
        scored_alerts = score_entities(df)
        
        # 3. Deduplicate & upsert alerts to prevent duplicate rows across ingestions
        entity_ids = [a.entity_id for a in scored_alerts]
        existing_alerts = db.query(Alert).filter(Alert.entity_id.in_(entity_ids)).all() if entity_ids else []
        existing_map = {(a.entity_id, a.entity_type): a for a in existing_alerts}

        for alert_data in scored_alerts:
            clean_reason = re.sub(r"^flagged due to:\s*", "", alert_data.reason or "", flags=re.IGNORECASE).strip()
            if not clean_reason:
                clean_reason = "Anomalous Bitcoin network pattern detected"

            key = (alert_data.entity_id, alert_data.entity_type)
            if key in existing_map:
                existing = existing_map[key]
                if alert_data.risk_score >= (existing.risk_score or 0):
                    existing.risk_score = alert_data.risk_score
                    existing.confidence = alert_data.confidence
                    existing.reason = clean_reason
                    existing.shap_explanation = alert_data.shap_explanation
            else:
                new_alert = Alert(
                    entity_type=alert_data.entity_type,
                    entity_id=alert_data.entity_id,
                    risk_score=alert_data.risk_score,
                    confidence=alert_data.confidence,
                    reason=clean_reason,
                    shap_explanation=alert_data.shap_explanation
                )
                db.add(new_alert)
                existing_map[key] = new_alert

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
