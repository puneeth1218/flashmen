"""
Raw Traffic & Transaction Data Ingestion Service (M2 to M1 Contract).
"""

import os
import pandas as pd
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError, ConfigDict
from datetime import datetime

class RawTransactionRow(BaseModel):
    """
    Pydantic v2 model to validate incoming data structures.
    Requires strict casting of amounts to floats and parses timestamps.
    """
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    txid: str
    input_addresses: str
    output_addresses: str
    input_amounts: float
    output_amounts: float
    
    # Ignore any additional unexpected columns from the raw file
    model_config = ConfigDict(extra="ignore")


def process_raw_file(filepath: str) -> pd.DataFrame:
    """
    Ingests and parses a raw CSV or JSON file containing Bitcoin network traffic logs.
    Iterates in chunks of 10,000 to prevent memory exhaustion and safely drops
    malformed rows that fail Pydantic validation.

    Args:
        filepath (str): Path to the uploaded raw data file (CSV or JSON).

    Returns:
        pd.DataFrame: Cleaned DataFrame containing validated rows.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at path: {filepath}")

    ext = os.path.splitext(filepath)[-1].lower()
    chunksize = 10000
    valid_records: List[Dict[str, Any]] = []

    def process_chunk(chunk: pd.DataFrame):
        records = chunk.to_dict(orient="records")
        for record in records:
            try:
                # 1. Pydantic validation and coercion
                validated = RawTransactionRow(**record)
                row_dict = validated.model_dump()
                
                # 2. Hardcode src_country and dst_country as 'unknown' per requirements
                row_dict["src_country"] = "unknown"
                row_dict["dst_country"] = "unknown"
                
                # Keep asn defaults if missing from raw data but required by downstream
                row_dict["src_asn"] = record.get("src_asn", "AS0")
                row_dict["dst_asn"] = record.get("dst_asn", "AS0")
                
                valid_records.append(row_dict)
            except ValidationError:
                # 3. Silently quarantine/drop malformed rows
                continue

    if ext == ".csv":
        for chunk in pd.read_csv(filepath, chunksize=chunksize):
            process_chunk(chunk)
    elif ext in [".json", ".jsonl"]:
        if ext == ".jsonl":
            for chunk in pd.read_json(filepath, lines=True, chunksize=chunksize):
                process_chunk(chunk)
        else:
            # Standard JSON array, read entirely then manually chunk
            df = pd.read_json(filepath)
            for i in range(0, len(df), chunksize):
                process_chunk(df.iloc[i:i+chunksize])
    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Must be CSV or JSON.")
    
    # 4. Concatenate the valid chunks and return the final DataFrame
    if not valid_records:
        # Return an empty DataFrame with the expected columns if everything failed
        final_df = pd.DataFrame(columns=[
            "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid",
            "input_addresses", "output_addresses", "input_amounts", "output_amounts",
            "src_asn", "src_country", "dst_asn", "dst_country"
        ])
    else:
        final_df = pd.DataFrame(valid_records)
        
    # Final guarantee that timestamps are proper pandas datetime objects localized to UTC
    if not final_df.empty:
        final_df["timestamp"] = pd.to_datetime(final_df["timestamp"], utc=True)
        
    return final_df
