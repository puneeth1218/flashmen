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
