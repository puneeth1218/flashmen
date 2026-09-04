import json
import logging
import os
from typing import List, Optional, Dict, Any, Union
import ast
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


def parse_list_field(val: Any, is_float: bool = False) -> List[Any]:
    """Helper to safely parse list fields from various formats (JSON string, Python repr, comma-delimited, single scalar)."""
    if isinstance(val, list):
        items = val
    elif pd.isna(val) or val is None or val == "":
        return []
    elif isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return []
        parsed = None
        # 1. Try JSON parsing
        try:
            p = json.loads(val_str)
            if isinstance(p, list):
                parsed = p
            elif not isinstance(p, (int, float)):
                parsed = [p]
        except Exception:
            pass

        # 2. Try python literal eval (e.g. ['addr1', 'addr2'])
        if parsed is None and val_str.startswith(("[", "(", "{")):
            try:
                p = ast.literal_eval(val_str)
                if isinstance(p, (list, tuple)):
                    parsed = list(p)
                elif not isinstance(p, (int, float)):
                    parsed = [p]
            except Exception:
                pass

        # 3. Fallback: comma-delimited or scalar string
        if parsed is None:
            clean = val_str.strip("[]()").strip()
            if "," in clean:
                parsed = [x.strip().strip("'\"") for x in clean.split(",") if x.strip()]
            else:
                parsed = [clean.strip("'\"")]
        items = parsed
    else:
        items = [val]

    if is_float:
        res = []
        for x in items:
            try:
                res.append(float(x))
            except (ValueError, TypeError):
                continue
        return res
    return [str(x) for x in items]


def process_raw_file(file_input: Union[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Parses CSV/JSON raw transaction data (from file path or pre-loaded DataFrame),
    validates schema using Pydantic, enriches with offline GeoIP metadata, and returns a clean pandas DataFrame.
    """
    # 1. Load Data
    if isinstance(file_input, pd.DataFrame):
        df_raw = file_input.copy()
    elif isinstance(file_input, str):
        if file_input.endswith('.csv'):
            df_raw = pd.read_csv(file_input)
        elif file_input.endswith('.json'):
            with open(file_input, 'r', encoding='utf-8') as f:
                records = json.load(f)
                if not isinstance(records, list):
                    raise ValueError("JSON file must contain a top-level array of objects.")
                df_raw = pd.DataFrame(records)
        else:
            raise ValueError("Unsupported file format. File must be .csv or .json")
    else:
        raise ValueError("Invalid input. Expected file path (str) or pandas DataFrame.")

    # Parse list columns if loading from CSV or stringified fields
    for col in ['input_addresses', 'output_addresses']:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].apply(lambda x: parse_list_field(x, is_float=False))
    for col in ['input_amounts', 'output_amounts']:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].apply(lambda x: parse_list_field(x, is_float=True))

    df_raw = df_raw.where(pd.notnull(df_raw), None)
    records = df_raw.to_dict(orient='records')
    # Ensure optional defaults are applied when None
    for r in records:
        if r.get('fee') is None:
            r['fee'] = 0.0
        if r.get('script_type') is None:
            r['script_type'] = "p2pkh"
        for str_col in ['timestamp', 'src_ip', 'dst_ip', 'txid']:
            if r.get(str_col) is not None and not isinstance(r[str_col], str):
                r[str_col] = str(r[str_col])
        for int_col in ['src_port', 'dst_port']:
            if r.get(int_col) is not None and not isinstance(r[int_col], int):
                try:
                    r[int_col] = int(float(r[int_col]))
                except (ValueError, TypeError):
                    pass

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
    possible_paths = [
        "data/geolite2/GeoLite2-City.mmdb",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "geolite2", "GeoLite2-City.mmdb"),
        "GeoLite2-City.mmdb",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "GeoLite2-City.mmdb"),
    ]
    geolite_path = next((p for p in possible_paths if os.path.isfile(p)), None)
    reader = None
    if geolite_path:
        try:
            reader = geoip2.database.Reader(geolite_path)
        except Exception as e:
            logger.info(f"Failed to open GeoLite2 database at {geolite_path}: {e}")

    try:
        df['src_country'] = df['src_ip'].apply(lambda ip: get_ip_metadata(ip, reader)['country'])
        df['dst_country'] = df['dst_ip'].apply(lambda ip: get_ip_metadata(ip, reader)['country'])
    finally:
        if reader is not None:
            reader.close()

    return df
