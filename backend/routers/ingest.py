"""
Ingestion Router: POST /api/v1/ingest
Handles file upload of raw Bitcoin traffic logs and triggers ingestion + scoring pipeline.
"""

import os
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from backend.services.ingestion import process_raw_file
from backend.services.scoring import score_entities

router = APIRouter(prefix="/api/v1", tags=["Ingest"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/synthetic")


@router.post("/ingest", status_code=202)
async def ingest_traffic_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Accepts raw CSV/JSON Bitcoin traffic log file upload, runs parsing pipeline,
    and returns processing status summary.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    try:
        df = process_raw_file(file_location)
        alerts = score_entities(df)
        
        return {
            "status": "success",
            "filename": file.filename,
            "processed_records": len(df),
            "generated_alerts_count": len(alerts),
            "message": f"Successfully ingested {len(df)} records and flagged {len(alerts)} suspicious entities."
        }
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process ingestion file: {str(e)}"
        )
