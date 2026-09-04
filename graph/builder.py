"""
NetworkX Graph Builder & Cytoscape Serializer (M4 to M5 Contract).
"""
# Updated by Arjun for MVP testing

import pandas as pd
import networkx as nx
from typing import Dict, Any, List
from graph.heuristics import add_heuristic_columns


class NetworkGraphBuilder:
    """
    Constructs a directed NetworkX graph from traffic/transaction records
    and serializes it to Cytoscape.js compatible format.
    """

    def __init__(self):
        self.G = nx.DiGraph()

    def add_dataframe_records(self, df: pd.DataFrame) -> None:
        """
        Populates graph with nodes (IPs, Wallets) and edges (Transactions, P2P Traffic).
        """
        for _, row in df.iterrows():
            src_ip = row.get("src_ip")
            dst_ip = row.get("dst_ip")
            txid = row.get("txid")
            
            # Check heuristics
            is_peel = row.get("is_peel_chain", False)
            is_mixer = row.get("is_mixer", False)
            
            tx_label_suffix = ""
            risk_score = 0.0
            if is_peel:
                tx_label_suffix = " (Peel Chain)"
                risk_score = 85.0
            elif is_mixer:
                tx_label_suffix = " (Mixer)"
                risk_score = 90.0
            
            if src_ip:
                self.G.add_node(str(src_ip), type="ip", label=f"IP: {src_ip}")
            if dst_ip:
                self.G.add_node(str(dst_ip), type="ip", label=f"IP: {dst_ip}")
                
            if src_ip and dst_ip:
                self.G.add_edge(str(src_ip), str(dst_ip), label="P2P Traffic", txid=str(txid or ""))

            # Process input and output wallets
            # Handle both list and comma-separated string cases
            in_addrs_raw = row.get("input_addresses")
            out_addrs_raw = row.get("output_addresses")
            
            in_addrs = in_addrs_raw if isinstance(in_addrs_raw, list) else str(in_addrs_raw or "").split(",")
            out_addrs = out_addrs_raw if isinstance(out_addrs_raw, list) else str(out_addrs_raw or "").split(",")
            
            for in_a in in_addrs:
                in_clean = str(in_a).strip()
                if in_clean:
                    self.G.add_node(in_clean, type="wallet", label=f"Wallet: {in_clean[:6]}...")
                    if txid:
                        tx_label = f"Tx: {str(txid)[:8]}..." + tx_label_suffix
                        self.G.add_node(str(txid), type="tx", label=tx_label, risk_score=risk_score)
                        self.G.add_edge(in_clean, str(txid), label="Input")

            for out_a in out_addrs:
                out_clean = str(out_a).strip()
                if out_clean:
                    self.G.add_node(out_clean, type="wallet", label=f"Wallet: {out_clean[:6]}...")
                    if txid:
                        tx_label = f"Tx: {str(txid)[:8]}..." + tx_label_suffix
                        self.G.add_node(str(txid), type="tx", label=tx_label, risk_score=risk_score)
                        self.G.add_edge(str(txid), out_clean, label="Output")

    def to_cytoscape_json(self) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
        """
        Contract 3 (M4 -> M5):
        Converts the internal NetworkX graph structure to Cytoscape JSON format.

        Returns:
            Dict[str, List[Dict[str, Dict[str, Any]]]]: Cytoscape JSON with 'nodes' and 'edges' key arrays:
            {"nodes": [{"data": {"id": "..."}}], "edges": [{"data": {"source": "...", "target": "..."}}]}
        """
        nodes_list = []
        for node_id, data in self.G.nodes(data=True):
            node_dict = {
                "id": str(node_id), 
                "label": data.get("label", str(node_id)), 
                "type": data.get("type", "unknown"),
                "risk_score": float(data.get("risk_score", 0.0))
            }
            nodes_list.append({"data": node_dict})

        edges_list = []
        for idx, (source, target, data) in enumerate(self.G.edges(data=True)):
            edge_id = f"e_{idx}_{source}_{target}"
            edge_dict = {
                "id": edge_id,
                "source": str(source),
                "target": str(target),
                "label": data.get("label", ""),
                "amount": float(data.get("amount", 0.0))
            }
            edges_list.append({"data": edge_dict})

        return {
            "nodes": nodes_list,
            "edges": edges_list
        }


def build_cytoscape_graph(df: pd.DataFrame) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
    """
    Utility wrapper function implementing Contract 3 directly from DataFrame input.
    """
    df_heuristics = add_heuristic_columns(df.copy())
    builder = NetworkGraphBuilder()
    builder.add_dataframe_records(df_heuristics)
    return builder.to_cytoscape_json()
