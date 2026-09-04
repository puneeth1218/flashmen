"""
Entity Anomaly Scoring & SHAP Explanation Service (M3 to M1 Contract).
Evaluates ingested traffic and transaction DataFrames using Isolation Forest
and topological feature engineering to generate dynamic risk alerts.
"""

import logging
import re
from typing import List, Dict, Literal, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ml.feature_engineering import extract_features, extract_wallet_features, WALLET_FEATURE_COLUMNS
from ml.model import IsolationForestAnomalyDetector, get_investigative_tag

logger = logging.getLogger(__name__)


class AlertData(BaseModel):
    """
    Pydantic contract for generated security alerts.
    """
    entity_type: Literal["wallet", "ip"] = Field(..., description="Type of entity ('wallet' or 'ip')")
    entity_id: str = Field(..., description="Unique entity identifier (Bitcoin address or IP address)")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score scaled between 0 and 100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")
    reason: str = Field(..., description="Human-readable explanation summary of the anomaly")
    shap_explanation: Dict[str, float] = Field(
        default_factory=dict, 
        description="Dictionary mapping feature names to SHAP values"
    )


def _sanitize_entity_id(raw_id: Any) -> str:
    """Cleans entity identifier to guarantee no brackets, quotes, or list artifacts."""
    if raw_id is None:
        return ""
    if isinstance(raw_id, (list, tuple)):
        raw_id = raw_id[0] if len(raw_id) > 0 else ""
    s = str(raw_id).strip()
    # Strip any brackets, braces, parentheses, quotes
    s = re.sub(r"^[\[\(\{\'\"]+|[\]\)\}\'\"]+$", "", s).strip()
    # If comma-separated within, take the first valid address
    if "," in s:
        parts = [p.strip().strip("'\"") for p in s.split(",") if p.strip()]
        s = parts[0] if parts else ""
    return s


def score_entities(df: pd.DataFrame) -> List[AlertData]:
    """
    Evaluates traffic/transaction DataFrame using ML feature pipeline and IsolationForest models.
    Produces calibrated risk scores, dynamic confidence intervals, and human-readable anomaly attribution.

    Contract 2 (M3 -> M1):
    Args:
        df (pd.DataFrame): Ingested normalized DataFrame (from process_raw_file).

    Returns:
        List[AlertData]: List of entity alert objects with risk scores (0-100), confidence, reasons, and SHAP values.
    """
    if df is None or df.empty:
        return []

    alerts: List[AlertData] = []
    seen_entities: set = set()

    # =========================================================================
    # 1. WALLET ANOMALY DETECTION (IsolationForest on Wallet Feature Space)
    # =========================================================================
    try:
        raw_wallet_df, _ = extract_wallet_features(df)
        if not raw_wallet_df.empty:
            num_wallets = len(raw_wallet_df)
            contamination = min(0.20, max(0.02, 5.0 / max(num_wallets, 1)))

            detector = IsolationForestAnomalyDetector(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            detector.fit(raw_wallet_df)
            scores = detector.score_samples(raw_wallet_df)

            for idx, (wallet_id, row) in enumerate(raw_wallet_df.iterrows()):
                clean_wallet = _sanitize_entity_id(wallet_id)
                if not clean_wallet or clean_wallet in seen_entities:
                    continue

                raw_score = float(scores[idx]) if idx < len(scores) else 50.0
                # Calculate dynamic confidence based on score extremities
                confidence = round(min(0.99, max(0.55, 0.50 + abs(raw_score - 50.0) / 100.0)), 2)

                # Generate attribution reason & breakdown
                try:
                    raw_reason = detector.get_anomaly_reason(row, top_n=2)
                    reason = re.sub(r"^flagged due to:\s*", "", str(raw_reason), flags=re.IGNORECASE).strip()
                    signals = detector.get_signal_breakdown(row, top_n=5)
                except Exception:
                    reason = "Unusual transaction volume or address fan-out pattern"
                    signals = {"tx_count": 0.5, "total_volume_out": 0.5}

                alerts.append(
                    AlertData(
                        entity_type="wallet",
                        entity_id=clean_wallet,
                        risk_score=round(raw_score, 1),
                        confidence=confidence,
                        reason=reason,
                        shap_explanation=signals
                    )
                )
                seen_entities.add(clean_wallet)
    except Exception as e:
        logger.warning(f"Wallet anomaly scoring failed: {e}")

    # =========================================================================
    # 2. IP ANOMALY DETECTION (IsolationForest on IP Topological Feature Space)
    # =========================================================================
    try:
        ip_features_df, _ = extract_features(df)
        if not ip_features_df.empty:
            ip_feature_cols = [
                "connection_count",
                "unique_dest_ips",
                "fan_out_ratio",
                "unique_ports",
                "non_standard_port_ratio"
            ]
            valid_cols = [c for c in ip_feature_cols if c in ip_features_df.columns]
            if valid_cols:
                num_ips = len(ip_features_df)
                contamination = min(0.20, max(0.02, 5.0 / max(num_ips, 1)))

                ip_detector = IsolationForestAnomalyDetector(
                    contamination=contamination,
                    random_state=42,
                    n_estimators=100
                )
                ip_matrix = ip_features_df[valid_cols].copy().fillna(0.0)
                ip_detector.fit(ip_matrix)
                ip_scores = ip_detector.score_samples(ip_matrix)

                for idx, row in ip_features_df.iterrows():
                    clean_ip = _sanitize_entity_id(row.get("entity_id"))
                    if not clean_ip or clean_ip == "UNKNOWN" or clean_ip in seen_entities:
                        continue

                    raw_score = float(ip_scores[idx]) if idx < len(ip_scores) else 50.0
                    confidence = round(min(0.99, max(0.55, 0.50 + abs(raw_score - 50.0) / 100.0)), 2)

                    try:
                        raw_reason = ip_detector.get_anomaly_reason(row[valid_cols], top_n=2)
                        reason = re.sub(r"^flagged due to:\s*", "", str(raw_reason), flags=re.IGNORECASE).strip()
                        signals = ip_detector.get_signal_breakdown(row[valid_cols], top_n=5)
                    except Exception:
                        reason = "High traffic fan-out rate across multiple non-standard ports"
                        signals = {"connection_count": 0.5, "unique_ports": 0.5}

                    alerts.append(
                        AlertData(
                            entity_type="ip",
                            entity_id=clean_ip,
                            risk_score=round(raw_score, 1),
                            confidence=confidence,
                            reason=reason,
                            shap_explanation=signals
                        )
                    )
                    seen_entities.add(clean_ip)
    except Exception as e:
        logger.warning(f"IP anomaly scoring failed: {e}")

    # Sort all alerts by risk score descending so the most critical anomalies appear first
    alerts.sort(key=lambda a: a.risk_score, reverse=True)
    return alerts
