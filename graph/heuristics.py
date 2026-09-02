"""
Graph Heuristics Module.
Detects transactional graph anomalies including peel-chains, change address heuristics, and CoinJoin/mixer structures.
"""
# Updated by Arjun for MVP testing
import pandas as pd
from typing import List, Dict, Any


def detect_peel_chains(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identifies peel-chain transfer patterns (transactions with 1 input and 2 outputs where one is a change output).

    Args:
        df (pd.DataFrame): Normalized transaction DataFrame.

    Returns:
        List[Dict[str, Any]]: List of identified peel-chain sequence descriptors.
    """
    peel_chains = []
    
    # Stub heuristic matching 1-in-2-out transactions
    for idx, row in df.iterrows():
        inputs = [i for i in str(row.get("input_addresses", "")).split(",") if i.strip()]
        outputs = [o for o in str(row.get("output_addresses", "")).split(",") if o.strip()]

        if len(inputs) == 1 and len(outputs) == 2:
            peel_chains.append({
                "txid": row.get("txid"),
                "peel_source_wallet": inputs[0],
                "recipient_wallet": outputs[0],
                "change_wallet": outputs[1],
                "confidence": 0.88,
                "pattern_type": "peel_chain"
            })

    return peel_chains


def detect_mixers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identifies privacy mixer / CoinJoin structures (e.g. transactions with N inputs and N equal-value outputs).

    Args:
        df (pd.DataFrame): Normalized transaction DataFrame.

    Returns:
        List[Dict[str, Any]]: List of identified mixer/CoinJoin transaction descriptors.
    """
    mixers = []

    for idx, row in df.iterrows():
        inputs = [i for i in str(row.get("input_addresses", "")).split(",") if i.strip()]
        outputs = [o for o in str(row.get("output_addresses", "")).split(",") if o.strip()]

        # Typical CoinJoin pattern: >= 3 inputs and >= 3 outputs
        if len(inputs) >= 3 and len(outputs) >= 3:
            mixers.append({
                "txid": row.get("txid"),
                "participant_count": len(inputs),
                "output_count": len(outputs),
                "confidence": 0.94,
                "pattern_type": "coinjoin_mixer"
            })

    return mixers

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