"""
Feature Engineering Pipeline (Module M3).
Transforms ingested transaction DataFrames into wallet-level numerical feature matrices
for Isolation Forest anomaly detection and IP-level topological feature vectors.
"""

import json
import logging
from typing import Tuple, List, Dict, Any, Set
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

WALLET_FEATURE_COLUMNS = [
    "tx_count",
    "total_volume_in",
    "total_volume_out",
    "fan_out_ratio",
    "fan_in_ratio",
    "unique_ips_used",
]


def _safe_parse_list(val: Any) -> List[Any]:
    """Helper to parse list, JSON-serialized list, or comma-separated string."""
    if isinstance(val, list):
        return val
    if val is None or pd.isna(val):
        return []
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return []
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback to comma-separated values
        return [item.strip() for item in val.split(",") if item.strip()]
    return [val]


def _safe_parse_float_list(val: Any) -> List[float]:
    """Helper to parse float list safely."""
    raw_list = _safe_parse_list(val)
    result = []
    for item in raw_list:
        try:
            result.append(float(item))
        except (ValueError, TypeError):
            result.append(0.0)
    return result


def extract_wallet_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Extracts wallet-level aggregated metrics from an ingested transaction DataFrame,
    cleans values (handling zero division, NaN, inf), and scales features via StandardScaler.

    Aggregated Metrics:
        - tx_count: Total transactions involving the wallet (sender or receiver).
        - total_volume_in: Total incoming BTC/satoshis (from output amounts directed to wallet).
        - total_volume_out: Total outgoing BTC/satoshis (from input amounts spent by wallet).
        - fan_out_ratio: Ratio of unique outputs to unique inputs (detects peel chains).
        - fan_in_ratio: Ratio of unique inputs to unique outputs (detects mixers/consolidation).
        - unique_ips_used: Distinct count of src_ip values associated with the wallet.

    Args:
        df (pd.DataFrame): Ingested transaction DataFrame from backend.services.ingestion.process_raw_file

    Returns:
        Tuple[pd.DataFrame, np.ndarray]:
            - raw_wallet_df: Aggregated DataFrame indexed by wallet_id with columns WALLET_FEATURE_COLUMNS.
            - scaled_matrix: StandardScaler-normalized 2D numpy array ready for IsolationForest.
    """
    if df is None or df.empty:
        raw_empty = pd.DataFrame(
            columns=WALLET_FEATURE_COLUMNS,
            index=pd.Index([], name="wallet_id"),
            dtype=float
        )
        return raw_empty, np.empty((0, len(WALLET_FEATURE_COLUMNS)), dtype=float)

    # Per-wallet tracking accumulators
    wallet_tx_ids: Dict[str, Set[str]] = {}
    wallet_vol_in: Dict[str, float] = {}
    wallet_vol_out: Dict[str, float] = {}
    wallet_ips: Dict[str, Set[str]] = {}
    wallet_tx_inputs: Dict[str, Set[str]] = {}
    wallet_tx_outputs: Dict[str, Set[str]] = {}

    def _init_wallet(w: str):
        if w not in wallet_tx_ids:
            wallet_tx_ids[w] = set()
            wallet_vol_in[w] = 0.0
            wallet_vol_out[w] = 0.0
            wallet_ips[w] = set()
            wallet_tx_inputs[w] = set()
            wallet_tx_outputs[w] = set()

    for _, row in df.iterrows():
        txid = str(row.get("txid", ""))
        src_ip = row.get("src_ip")
        src_ip_str = str(src_ip).strip() if (src_ip and not pd.isna(src_ip) and src_ip != "UNKNOWN") else None

        input_addrs = [str(a).strip() for a in _safe_parse_list(row.get("input_addresses")) if str(a).strip()]
        input_amts = _safe_parse_float_list(row.get("input_amounts"))
        output_addrs = [str(a).strip() for a in _safe_parse_list(row.get("output_addresses")) if str(a).strip()]
        output_amts = _safe_parse_float_list(row.get("output_amounts"))

        # Align input addresses with input amounts (fill missing amounts with 0.0)
        in_amt_len = len(input_amts)
        aligned_inputs = []
        for i, addr in enumerate(input_addrs):
            amt = input_amts[i] if i < in_amt_len else 0.0
            aligned_inputs.append((addr, amt))

        # Align output addresses with output amounts (fill missing amounts with 0.0)
        out_amt_len = len(output_amts)
        aligned_outputs = []
        for i, addr in enumerate(output_addrs):
            amt = output_amts[i] if i < out_amt_len else 0.0
            aligned_outputs.append((addr, amt))

        # Set of all unique input & output addresses for this transaction
        unique_tx_inputs = set(input_addrs)
        unique_tx_outputs = set(output_addrs)
        all_tx_wallets = unique_tx_inputs.union(unique_tx_outputs)

        # Process outgoing flow for input wallets
        for addr, amt in aligned_inputs:
            _init_wallet(addr)
            wallet_vol_out[addr] += amt

        # Process incoming flow for output wallets
        for addr, amt in aligned_outputs:
            _init_wallet(addr)
            wallet_vol_in[addr] += amt

        # Update transaction participation, IP tracking, and ratio sets
        for w in all_tx_wallets:
            _init_wallet(w)
            if txid:
                wallet_tx_ids[w].add(txid)
            if src_ip_str:
                wallet_ips[w].add(src_ip_str)
            wallet_tx_inputs[w].update(unique_tx_inputs)
            wallet_tx_outputs[w].update(unique_tx_outputs)

    all_wallets = sorted(list(wallet_tx_ids.keys()))
    if not all_wallets:
        raw_empty = pd.DataFrame(
            columns=WALLET_FEATURE_COLUMNS,
            index=pd.Index([], name="wallet_id"),
            dtype=float
        )
        return raw_empty, np.empty((0, len(WALLET_FEATURE_COLUMNS)), dtype=float)

    rows = []
    for w in all_wallets:
        tx_count = float(len(wallet_tx_ids[w]))
        vol_in = float(wallet_vol_in[w])
        vol_out = float(wallet_vol_out[w])
        n_in = float(len(wallet_tx_inputs[w]))
        n_out = float(len(wallet_tx_outputs[w]))

        # fan_out_ratio: unique outputs / unique inputs
        fan_out = (n_out / n_in) if n_in > 0 else 0.0
        # fan_in_ratio: unique inputs / unique outputs
        fan_in = (n_in / n_out) if n_out > 0 else 0.0
        unique_ips = float(len(wallet_ips[w]))

        rows.append({
            "wallet_id": w,
            "tx_count": tx_count,
            "total_volume_in": vol_in,
            "total_volume_out": vol_out,
            "fan_out_ratio": fan_out,
            "fan_in_ratio": fan_in,
            "unique_ips_used": unique_ips,
        })

    raw_wallet_df = pd.DataFrame(rows).set_index("wallet_id")
    raw_wallet_df = raw_wallet_df[WALLET_FEATURE_COLUMNS]

    # Data Sanitization: replace NaN, inf, -inf with 0.0
    raw_wallet_df = raw_wallet_df.replace([np.inf, -np.inf], 0.0).fillna(0.0)

    # Scaling with StandardScaler
    if len(raw_wallet_df) == 1:
        scaled_matrix = np.zeros((1, len(WALLET_FEATURE_COLUMNS)), dtype=float)
    else:
        scaler = StandardScaler()
        scaled_matrix = scaler.fit_transform(raw_wallet_df)
        scaled_matrix = np.nan_to_num(scaled_matrix, nan=0.0, posinf=0.0, neginf=0.0)

    return raw_wallet_df, scaled_matrix


def extract_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dual extraction interface producing IP-level and Wallet-level feature sets.
    Maintains full compatibility with existing services, graph, and test suites.

    Args:
        df (pd.DataFrame): Ingested normalized transaction DataFrame.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (ip_features_df, wallet_features_df)
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # --- IP Feature Engineering ---
    ip_records = []
    unique_ips = set(df["src_ip"].dropna().unique()).union(set(df["dst_ip"].dropna().unique()))

    for ip in unique_ips:
        if not ip or ip == "UNKNOWN":
            continue
        out_bound = df[df["src_ip"] == ip]
        in_bound = df[df["dst_ip"] == ip]
        
        connection_count = len(out_bound) + len(in_bound)
        unique_dest_ips = len(out_bound["dst_ip"].unique()) if not out_bound.empty else 0
        unique_ports = len(set(out_bound["dst_port"].unique()).union(set(in_bound["src_port"].unique())))
        non_standard_port_ratio = 0.15 if unique_ports > 3 else 0.02
        
        ip_records.append({
            "entity_id": ip,
            "connection_count": connection_count,
            "unique_dest_ips": unique_dest_ips,
            "fan_out_ratio": unique_dest_ips / max(1, connection_count),
            "unique_ports": unique_ports,
            "non_standard_port_ratio": non_standard_port_ratio,
        })

    ip_features_df = pd.DataFrame(ip_records)

    # --- Wallet Feature Engineering (Real Aggregations) ---
    raw_wallet_df, _ = extract_wallet_features(df)
    if not raw_wallet_df.empty:
        wallet_features_df = raw_wallet_df.reset_index().rename(columns={"wallet_id": "entity_id"})
        # Retain heuristic indicator for graph compatibility
        wallet_features_df["peel_chain_depth"] = (wallet_features_df["fan_out_ratio"] > 1.5).astype(int)
    else:
        wallet_features_df = pd.DataFrame()

    return ip_features_df, wallet_features_df
