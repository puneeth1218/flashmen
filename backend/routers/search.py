import os
import glob
from typing import List
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
from backend.services.database import get_db, Alert

router = APIRouter(prefix="/api/v1", tags=["Search"])


class SearchResultItem(BaseModel):
    entity_type: str = Field(..., description="Type of entity ('wallet', 'ip', 'txid')")
    entity_id: str = Field(..., description="Identifier matched")
    risk_score: float = Field(0.0, description="Associated risk score if evaluated")
    summary: str = Field("", description="Short summary description")


class SearchResponse(BaseModel):
    query: str
    results_count: int
    results: List[SearchResultItem]


@router.get("/search", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search term (IP, Wallet address, or TxID)"),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Performs global lookup matching search query against active alerts database and ingested telemetry.
    """
    query_str = q.strip()
    results: List[SearchResultItem] = []
    seen = set()

    # 1. Search database alerts table for matching entity_id
    matched_alerts = (
        db.query(Alert)
        .filter(Alert.entity_id.ilike(f"%{query_str}%"))
        .order_by(desc(Alert.risk_score), desc(Alert.created_at))
        .limit(20)
        .all()
    )

    for a in matched_alerts:
        clean_id = str(a.entity_id).strip()
        key = (clean_id, a.entity_type)
        if key in seen:
            continue
        seen.add(key)
        reason_text = a.reason or "Anomalous Bitcoin network pattern detected"
        summary = f"Flagged {a.entity_type.upper()} ({float(a.risk_score):.1f}/100): {reason_text}"
        results.append(
            SearchResultItem(
                entity_type=a.entity_type,
                entity_id=clean_id,
                risk_score=round(float(a.risk_score), 1) if a.risk_score is not None else 0.0,
                summary=summary
            )
        )

    # 2. If no alerts found (or to complement), check the latest ingested DataFrame for unflagged/benign records
    if len(results) == 0:
        UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/synthetic")
        if os.path.exists(UPLOAD_DIR):
            files = glob.glob(os.path.join(UPLOAD_DIR, "*"))
            data_files = [f for f in files if f.endswith(('.csv', '.json', '.jsonl')) and not os.path.basename(f).startswith('.')]
            if data_files:
                try:
                    latest_file = max(data_files, key=os.path.getmtime)
                    if latest_file.endswith('.csv'):
                        df = pd.read_csv(latest_file)
                    else:
                        df = pd.read_json(latest_file)

                    # Check txid
                    if 'txid' in df.columns:
                        tx_matches = df[df['txid'].astype(str).str.contains(query_str, case=False, na=False)].head(5)
                        for _, row in tx_matches.iterrows():
                            txid = str(row['txid']).strip()
                            if txid not in seen:
                                seen.add(txid)
                                results.append(
                                    SearchResultItem(
                                        entity_type="txid",
                                        entity_id=txid,
                                        risk_score=0.0,
                                        summary="Unflagged / Benign transaction telemetry observed in network traffic."
                                    )
                                )

                    # Check IP addresses
                    for col in ['src_ip', 'dst_ip']:
                        if col in df.columns:
                            ip_matches = df[df[col].astype(str).str.contains(query_str, case=False, na=False)].head(5)
                            for _, row in ip_matches.iterrows():
                                ip_val = str(row[col]).strip()
                                if ip_val not in seen and ip_val != "UNKNOWN":
                                    seen.add(ip_val)
                                    results.append(
                                        SearchResultItem(
                                            entity_type="ip",
                                            entity_id=ip_val,
                                            risk_score=0.0,
                                            summary="Unflagged / Benign peer IP node observed in network traffic."
                                        )
                                    )

                    # Check wallet addresses
                    for col in ['input_addresses', 'output_addresses']:
                        if col in df.columns:
                            addr_matches = df[df[col].astype(str).str.contains(query_str, case=False, na=False)].head(5)
                            for _, row in addr_matches.iterrows():
                                raw_val = str(row[col])
                                parts = [p.strip().strip("'\"[]()") for p in raw_val.split(',') if query_str.lower() in p.lower()]
                                for p in parts[:2]:
                                    if p and p not in seen:
                                        seen.add(p)
                                        results.append(
                                            SearchResultItem(
                                                entity_type="wallet",
                                                entity_id=p,
                                                risk_score=0.0,
                                                summary="Unflagged / Benign Bitcoin wallet observed in network traffic."
                                            )
                                        )
                except Exception:
                    pass

    return SearchResponse(
        query=q,
        results_count=len(results),
        results=results
    )
