import json
import logging
from typing import List, Optional, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
import geoip2.database

# Setup logger
logger = logging.getLogger(__name__)

# Global cache to optimize GeoIP lookups
GEOIP_CACHE: Dict[str, Dict[str, str]] = {}


class RawTransactionRow(BaseModel):
    """Pydantic v2 Schema for validating incoming Bitcoin metadata rows."""
    timestamp: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    txid: str
    input_addresses: List[str]
    output_addresses: List[str]
    input_amounts: List[float]
    output_amounts: List[float]
    fee: Optional[float] = 0.0
    script_type: Optional[str] = "p2pkh"


def get_ip_metadata(ip_address: str, reader: Optional[geoip2.database.Reader]) -> Dict[str, str]:
    """Helper to look up IP country via MaxMind with local caching."""
    if ip_address in GEOIP_CACHE:
        return GEOIP_CACHE[ip_address]

    result = {"country": "UNKNOWN"}
    
    if reader is not None:
        try:
            response = reader.city(ip_address)
            if response.country and response.country.iso_code:
                result["country"] = response.country.iso_code
        except Exception:
            # Private IPs, loopbacks, or unmapped IPs fall back gracefully
            pass

    GEOIP_CACHE[ip_address] = result
    return result


def process_raw_file(filepath: str) -> pd.DataFrame:
    """
    Parses CSV/JSON raw transaction data, validates schema using Pydantic,
    enriches with offline GeoIP metadata, and returns a clean pandas DataFrame.
    """
    # 1. Load Data
    if filepath.endswith('.csv'):
        df_raw = pd.read_csv(filepath)
        # Parse stringified list columns if loading from CSV
        for col in ['input_addresses', 'output_addresses', 'input_amounts', 'output_amounts']:
            if col in df_raw.columns:
                df_raw[col] = df_raw[col].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
                )
        records = df_raw.to_dict(orient='records')
    elif filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            records = json.load(f)
            if not isinstance(records, list):
                raise ValueError("JSON file must contain a top-level array of objects.")
    else:
        raise ValueError("Unsupported file format. File must be .csv or .json")

    # 2. Validate Rows via Pydantic
    validated_records = []
    for idx, record in enumerate(records):
        try:
            validated_row = RawTransactionRow(**record)
            validated_records.append(validated_row.model_dump())
        except ValidationError as e:
            logger.warning(f"Row {idx} dropped due to schema validation failure: {e}")

    if not validated_records:
        raise ValueError("No valid records found after Pydantic schema validation.")

    df = pd.DataFrame(validated_records)

    # 3. Standardize Timestamp to UTC
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # 4. Perform GeoIP Enrichment
    geolite_path = "data/geolite2/GeoLite2-City.mmdb"
    reader = None
    try:
        reader = geoip2.database.Reader(geolite_path)
    except FileNotFoundError:
        logger.info("GeoLite2-City.mmdb not found. Falling back to default 'UNKNOWN' countries.")

    try:
        df['src_country'] = df['src_ip'].apply(lambda ip: get_ip_metadata(ip, reader)['country'])
        df['dst_country'] = df['dst_ip'].apply(lambda ip: get_ip_metadata(ip, reader)['country'])
    finally:
        if reader is not None:
            reader.close()

    return df