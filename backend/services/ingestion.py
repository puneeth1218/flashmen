"""
Raw Traffic & Transaction Data Ingestion Service (M2 to M1 Contract).
"""

import os
import pandas as pd
from typing import List

# Contract Required Columns
REQUIRED_COLUMNS: List[str] = [
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "txid",
    "input_addresses",
    "output_addresses",
    "input_amounts",
    "output_amounts",
    "src_asn",
    "src_country",
    "dst_asn",
    "dst_country",
]


def process_raw_file(filepath: str) -> pd.DataFrame:
    """
    Ingests and parses a raw CSV or JSON file containing Bitcoin network traffic logs.

    Contract 1 (M2 -> M1):
    Args:
        filepath (str): Path to the uploaded raw data file (CSV or JSON).

    Returns:
        pd.DataFrame: Cleaned DataFrame containing exact columns:
            [timestamp, src_ip, dst_ip, src_port, dst_port, txid,
             input_addresses, output_addresses, input_amounts, output_amounts,
             src_asn, src_country, dst_asn, dst_country]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at path: {filepath}")

    ext = os.path.splitext(filepath)[-1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath)
    elif ext in [".json", ".jsonl"]:
        df = pd.read_json(filepath, lines=(ext == ".jsonl"))
    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Must be CSV or JSON.")

    # Ensure all required contract columns exist, setting missing ones to default stubs
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if "asn" in col:
                df[col] = "AS0"
            elif "country" in col:
                df[col] = "UNKNOWN"
            elif "port" in col:
                df[col] = 8333
            elif "amounts" in col or "addresses" in col:
                df[col] = ""
            else:
                df[col] = None

    # Cast timestamp to ISO format string or datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").astype(str)
    
    # Filter to exact contract schema ordering
    cleaned_df = df[REQUIRED_COLUMNS].copy()
    
    return cleaned_df
