"""
Faker-based Synthetic Bitcoin Traffic Dataset Generator.
Generates test datasets with realistic IP addresses, ASN numbers, GeoIP data, and Bitcoin transactions.
"""

import argparse
import random
import time
import pandas as pd
from typing import List, Dict, Any

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None


def generate_synthetic_dataset(num_records: int = 100, seed: int = None) -> pd.DataFrame:
    """
    Generates a synthetic DataFrame matching Contract 1 schema requirements.

    Args:
        num_records (int): Number of synthetic traffic rows to generate.
        seed (int): Optional random seed for reproducibility.

    Returns:
        pd.DataFrame: Synthetic dataset dataframe.
    """
    if seed is not None:
        random.seed(seed)
        if fake:
            Faker.seed(seed)

    records: List[Dict[str, Any]] = []
    
    countries = ["US", "DE", "CN", "RU", "NL", "JP", "BR", "GB"]
    asns = ["AS15169", "AS16509", "AS13335", "AS7018", "AS24940"]

    for i in range(num_records):
        is_anomaly = random.random() < 0.05
        pattern_type = "normal"
        
        if is_anomaly:
            pattern_type = random.choice(["peel_chain", "mixer", "ip_spoof"])
            
        src_ip = fake.ipv4() if fake else f"192.168.1.{random.randint(1, 254)}"
        dst_ip = fake.ipv4() if fake else f"10.0.0.{random.randint(1, 254)}"
        
        src_port = random.choice([8333, 8332, 18333, 49152, 50124])
        dst_port = 8333
        
        # Sample bitcoin address stubs
        src_addr = f"1{random.randint(100000000000000000, 999999999999999999)}"
        dst_addr = f"3{random.randint(100000000000000000, 999999999999999999)}"
        
        input_amount = round(random.uniform(0.01, 5.0), 8)
        output_amount = round(random.uniform(0.01, input_amount - 0.0001), 8)
        
        if pattern_type == "peel_chain":
            output_amount = round(input_amount - 0.001, 8)
        elif pattern_type == "mixer":
            src_addr = f"1{random.randint(10000000, 99999999)},1{random.randint(10000000, 99999999)}"
            dst_addr = f"3{random.randint(10000000, 99999999)},3{random.randint(10000000, 99999999)}"
        elif pattern_type == "ip_spoof":
            src_ip = "127.0.0.1"
        
        records.append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "txid": f"{random.getrandbits(256):064x}",
            "input_addresses": src_addr,
            "output_addresses": dst_addr,
            "input_amounts": f"{input_amount}",
            "output_amounts": f"{output_amount}",
            "src_asn": random.choice(asns),
            "src_country": random.choice(countries),
            "dst_asn": random.choice(asns),
            "dst_country": random.choice(countries),
            "pattern_type": pattern_type,
            "entity_id": f"wallet_{i:05d}"
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Bitcoin traffic dataset")
    parser.add_argument("--output", type=str, default="../data/synthetic/sample_traffic.csv", help="Output file path")
    parser.add_argument("--rows", type=int, default=500, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    print(f"Generating {args.rows} synthetic records with seed {args.seed}...")
    df_synthetic = generate_synthetic_dataset(args.rows, args.seed)
    df_synthetic.to_csv(args.output, index=False)
    print(f"Dataset saved to {args.output}")
