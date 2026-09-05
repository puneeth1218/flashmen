"""
Graph Heuristics Module.
Detects transactional graph anomalies including peel-chains, change address heuristics, and CoinJoin/mixer structures.
"""
# Updated by Arjun for MVP testing
import pandas as pd
from typing import List, Dict, Any


import pandas as pd

def get_count(val):
    """
    Safely counts address entries whether stored as a Python list,
    comma-separated string, or scalar.
    """
    if isinstance(val, list):
        return len(val)
    if isinstance(val, str):
        return len([x for x in val.split(',') if x.strip()])
    if pd.isna(val) or val is None:
        return 0
    return 1


def add_heuristic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates transactional graph heuristics (peel-chain, mixer).
    Safely handles both list and string address formats.
    """
    if 'input_addresses' not in df.columns or 'output_addresses' not in df.columns:
        df['is_peel_chain'] = False
        df['is_mixer'] = False
        return df

    in_count = df['input_addresses'].apply(get_count)
    out_count = df['output_addresses'].apply(get_count)

    # Peel Chain Detection: 1 Input, 2 Outputs (payment + change)
    df['is_peel_chain'] = (in_count == 1) & (out_count == 2)

    # Mixer Detection: >= 3 Inputs, >= 3 Outputs (CoinJoin consolidation)
    df['is_mixer'] = (in_count >= 3) & (out_count >= 3)

    return df

def extract_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    M4 -> M3 Contract: 
    Extracts graph-derived features (unique_ips_used, wallets_per_ip) 
    to pass back to the ML pipeline.
    """
    features = []

    # Clean and explode the input addresses so each wallet gets its own row mapping to an IP
    # This simulates traversing the Graph path: Wallet -> Transaction -> IP
    temp_df = df[['src_ip', 'input_addresses']].dropna().copy()
    temp_df['wallet'] = temp_df['input_addresses'].apply(
        lambda val: val if isinstance(val, list) else [x.strip() for x in str(val).split(',') if x.strip()]
    )
    exploded_df = temp_df.explode('wallet')
    exploded_df['wallet'] = exploded_df['wallet'].astype(str).str.strip()
    exploded_df = exploded_df[exploded_df['wallet'] != ""]

    # Metric 1: unique_ips_used (Wallet Feature)
    # Normal wallets use 1-2 IPs; automated/mixer wallets use many
    wallet_ip_counts = exploded_df.groupby('wallet')['src_ip'].nunique().reset_index()
    wallet_ip_counts.rename(columns={'src_ip': 'unique_ips_used', 'wallet': 'entity_id'}, inplace=True)
    wallet_ip_counts['entity_type'] = 'wallet'

    # Metric 2: wallets_per_ip (IP Feature)
    # One IP broadcasting for many wallets = exchange, botnet, or mixer
    ip_wallet_counts = exploded_df.groupby('src_ip')['wallet'].nunique().reset_index()
    ip_wallet_counts.rename(columns={'wallet': 'wallets_per_ip', 'src_ip': 'entity_id'}, inplace=True)
    ip_wallet_counts['entity_type'] = 'ip'

    # Combine both feature sets into a single table for M3
    final_features = pd.concat([wallet_ip_counts, ip_wallet_counts], ignore_index=True)
    
    return final_features