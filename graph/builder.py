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
            
            # Check heuristics and pattern types
            is_peel = bool(row.get("is_peel_chain", False))
            is_mixer = bool(row.get("is_mixer", False))
            raw_pattern = str(row.get("pattern_type", "")).lower().strip()
            
            if raw_pattern == "peel_chain":
                is_peel = True
            elif raw_pattern == "mixer":
                is_mixer = True

            tx_label_suffix = ""
            risk_score = 0.0
            pattern_tag = ""
            if is_peel:
                tx_label_suffix = " (Peel Chain)"
                risk_score = 85.0
                pattern_tag = "Peel Chain"
            elif is_mixer:
                tx_label_suffix = " (Mixer)"
                risk_score = 90.0
                pattern_tag = "Mixer"
            elif raw_pattern and raw_pattern not in ["normal", "benign", "nan"]:
                formatted_pattern = raw_pattern.replace('_', ' ').title()
                tx_label_suffix = f" ({formatted_pattern})"
                risk_score = 80.0
                pattern_tag = formatted_pattern
            
            if src_ip:
                s_ip = str(src_ip)
                if s_ip not in self.G:
                    self.G.add_node(s_ip, type="ip", label=f"IP: {s_ip}", risk_score=0.0, pattern_tag="")
            if dst_ip:
                d_ip = str(dst_ip)
                if d_ip not in self.G:
                    self.G.add_node(d_ip, type="ip", label=f"IP: {d_ip}", risk_score=0.0, pattern_tag="")
                
            if src_ip and dst_ip:
                self.G.add_edge(str(src_ip), str(dst_ip), label="P2P Traffic", txid=str(txid or ""), amount=0.0)

            # Process input and output wallets
            # Handle both list and comma-separated string cases
            in_addrs_raw = row.get("input_addresses")
            out_addrs_raw = row.get("output_addresses")
            
            in_addrs = in_addrs_raw if isinstance(in_addrs_raw, list) else [x.strip() for x in str(in_addrs_raw or "").split(",") if x.strip()]
            out_addrs = out_addrs_raw if isinstance(out_addrs_raw, list) else [x.strip() for x in str(out_addrs_raw or "").split(",") if x.strip()]

            in_amts_raw = row.get("input_amounts")
            out_amts_raw = row.get("output_amounts")
            in_amts = in_amts_raw if isinstance(in_amts_raw, list) else []
            out_amts = out_amts_raw if isinstance(out_amts_raw, list) else []
            
            if txid:
                txid_str = str(txid)
                tx_label = f"Tx: {txid_str[:8]}...{tx_label_suffix}"
                self.G.add_node(txid_str, type="tx", label=tx_label, risk_score=risk_score, pattern_tag=pattern_tag)

                for idx, in_a in enumerate(in_addrs):
                    in_clean = str(in_a).strip()
                    if in_clean:
                        prev_risk = self.G.nodes[in_clean].get("risk_score", 0.0) if in_clean in self.G else 0.0
                        w_risk = max(prev_risk, (risk_score * 0.9) if (is_peel or is_mixer) else 0.0)
                        prev_tag = self.G.nodes[in_clean].get("pattern_tag", "") if in_clean in self.G else ""
                        w_tag = pattern_tag if (is_peel or is_mixer) and not prev_tag else (prev_tag or pattern_tag)
                        
                        self.G.add_node(in_clean, type="wallet", label=f"Wallet: {in_clean[:6]}...", risk_score=w_risk, pattern_tag=w_tag)
                        amt = float(in_amts[idx]) if idx < len(in_amts) else 0.0
                        self.G.add_edge(in_clean, txid_str, label="Input", amount=amt)

                for idx, out_a in enumerate(out_addrs):
                    out_clean = str(out_a).strip()
                    if out_clean:
                        prev_risk = self.G.nodes[out_clean].get("risk_score", 0.0) if out_clean in self.G else 0.0
                        w_risk = max(prev_risk, (risk_score * 0.9) if (is_peel or is_mixer) else 0.0)
                        prev_tag = self.G.nodes[out_clean].get("pattern_tag", "") if out_clean in self.G else ""
                        w_tag = pattern_tag if (is_peel or is_mixer) and not prev_tag else (prev_tag or pattern_tag)

                        self.G.add_node(out_clean, type="wallet", label=f"Wallet: {out_clean[:6]}...", risk_score=w_risk, pattern_tag=w_tag)
                        amt = float(out_amts[idx]) if idx < len(out_amts) else 0.0
                        self.G.add_edge(txid_str, out_clean, label="Output", amount=amt)

    def to_cytoscape_json(self) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
        """
        Contract 3 (M4 -> M5):
        Converts the internal NetworkX graph structure to Cytoscape JSON format.
        """
        return format_cytoscape_elements(self.G)


def format_cytoscape_elements(G: Any) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
    """
    Serializes a NetworkX graph or subgraph into Cytoscape.js nodes & edges format.
    """
    nodes_list = []
    for node_id, data in G.nodes(data=True):
        node_dict = {
            "id": str(node_id), 
            "label": data.get("label", str(node_id)), 
            "type": data.get("type", "unknown"),
            "risk_score": float(data.get("risk_score", 0.0)),
            "pattern_tag": str(data.get("pattern_tag", ""))
        }
        nodes_list.append({"data": node_dict})

    edges_list = []
    for idx, (source, target, data) in enumerate(G.edges(data=True)):
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


def build_cytoscape_graph(
    df: pd.DataFrame, 
    entity_id: Any = None, 
    depth: int = 2,
    max_nodes: int = 45
) -> Dict[str, List[Dict[str, Dict[str, Any]]]]:
    """
    Utility wrapper function implementing Contract 3 directly from DataFrame input.
    - When entity_id is specified: extracts ego-subgraph (radius=depth) around target node.
    - When entity_id is NOT specified (default view): isolates high-risk anomalous nodes
      (risk_score >= 70 or pattern_type != 'benign') and their 1-hop neighbors, capping
      the view at 40-50 nodes to avoid hairball distortion.
    """
    df_heuristics = add_heuristic_columns(df.copy())
    builder = NetworkGraphBuilder()
    builder.add_dataframe_records(df_heuristics)
    G = builder.G

    if entity_id:
        clean_entity_id = str(entity_id).strip()
        target_node = None
        if clean_entity_id in G:
            target_node = clean_entity_id
        else:
            for n in G.nodes():
                if str(n).lower() == clean_entity_id.lower():
                    target_node = n
                    break
        if target_node is None:
            for n in G.nodes():
                if clean_entity_id.lower() in str(n).lower():
                    target_node = n
                    break

        if target_node is not None:
            subgraph = nx.ego_graph(G, n=target_node, radius=depth, undirected=True)
            return format_cytoscape_elements(subgraph)
        else:
            return {"nodes": [], "edges": []}

    # Default view: Filter to high-risk anomalous nodes and their immediate 1-hop neighbors
    G_undir = G.to_undirected()
    high_risk_candidates = [
        n for n, d in G.nodes(data=True)
        if float(d.get("risk_score", 0.0)) >= 70.0 or (d.get("pattern_tag") and d.get("pattern_tag") not in ["", "benign", "normal"])
    ]

    high_risk_candidates.sort(
        key=lambda n: (float(G.nodes[n].get("risk_score", 0.0)), G.degree(n)),
        reverse=True
    )

    selected_nodes = set()
    if high_risk_candidates:
        for seed in high_risk_candidates:
            selected_nodes.add(seed)
            for nbr in G_undir.neighbors(seed):
                selected_nodes.add(nbr)
                if len(selected_nodes) >= max_nodes:
                    break
            if len(selected_nodes) >= max_nodes:
                break

        if len(selected_nodes) > max_nodes:
            ranked_subset = sorted(
                selected_nodes,
                key=lambda n: (float(G.nodes[n].get("risk_score", 0.0)), G.degree(n)),
                reverse=True
            )[:max_nodes]
            selected_nodes = set(ranked_subset)
    else:
        # Fallback if no high-risk nodes exist
        ranked_nodes = sorted(
            G.nodes(data=True),
            key=lambda item: (float(item[1].get("risk_score", 0.0)), G.degree(item[0])),
            reverse=True
        )[:max_nodes]
        selected_nodes = set(n for n, _ in ranked_nodes)

    subgraph = G.subgraph(selected_nodes).copy()
    return format_cytoscape_elements(subgraph)
