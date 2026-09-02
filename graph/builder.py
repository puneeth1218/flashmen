"""
NetworkX Graph Builder & Cytoscape Serializer (M4 to M5 Contract).
"""

import pandas as pd
import networkx as nx
from typing import Dict, Any, List


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
            
            if src_ip:
                self.G.add_node(str(src_ip), type="ip", label=f"IP: {src_ip}")
            if dst_ip:
                self.G.add_node(str(dst_ip), type="ip", label=f"IP: {dst_ip}")
                
            if src_ip and dst_ip:
                self.G.add_edge(str(src_ip), str(dst_ip), label="P2P Traffic", txid=str(txid or ""))

            # Process input and output wallets
            in_addrs = str(row.get("input_addresses") or "").split(",")
            out_addrs = str(row.get("output_addresses") or "").split(",")
            
            for in_a in in_addrs:
                in_clean = in_a.strip()
                if in_clean:
                    self.G.add_node(in_clean, type="wallet", label=f"Wallet: {in_clean[:6]}...")
                    if txid:
                        self.G.add_node(str(txid), type="tx", label=f"Tx: {str(txid)[:8]}...")
                        self.G.add_edge(in_clean, str(txid), label="Input")

            for out_a in out_addrs:
                out_clean = out_a.strip()
                if out_clean:
                    self.G.add_node(out_clean, type="wallet", label=f"Wallet: {out_clean[:6]}...")
                    if txid:
                        self.G.add_node(str(txid), type="tx", label=f"Tx: {str(txid)[:8]}...")
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
            node_dict = {"id": str(node_id), "label": data.get("label", str(node_id)), "type": data.get("type", "unknown")}
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
    builder = NetworkGraphBuilder()
    builder.add_dataframe_records(df)
    return builder.to_cytoscape_json()
