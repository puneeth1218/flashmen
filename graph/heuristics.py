"""
Graph Heuristics Module.
Detects transactional graph anomalies including peel-chains, change address heuristics, and CoinJoin/mixer structures.
"""
# Updated by Arjun for MVP testing
import pandas as pd
from typing import List, Dict, Any


import pandas as pd

def add_heuristic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strong Tier M4 -> M3 Contract: 
    Replaces slow iterrows() with vectorized operations to handle 50k+ rows.
    Adds boolean heuristic flags as direct columns for the ML model.
    """
    # 1. Clean the address columns (handle NaN values)
    inputs = df['input_addresses'].fillna('')
    outputs = df['output_addresses'].fillna('')

    # 2. Vectorized Counting: number of addresses = commas + 1 
    # (If the string is empty, the count is 0)
    in_count = inputs.str.count(',') + 1
    in_count = in_count.where(inputs != '', 0)
    
    out_count = outputs.str.count(',') + 1
    out_count = out_count.where(outputs != '', 0)

    # 3. Vectorized Peel Chain Detection (1 Input, 2 Outputs)
    df['is_peel_chain'] = (in_count == 1) & (out_count == 2)

    # 4. Vectorized Mixer Detection (e.g., >= 3 Inputs, >= 3 Outputs)
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
    temp_df['wallet'] = temp_df['input_addresses'].astype(str).str.split(',')
    exploded_df = temp_df.explode('wallet')
    exploded_df['wallet'] = exploded_df['wallet'].str.strip()
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