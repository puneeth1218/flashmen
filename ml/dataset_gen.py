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


def generate_synthetic_dataset(num_records: int = 100) -> pd.DataFrame:
    """
    Generates a synthetic DataFrame matching Contract 1 schema requirements.

    Args:
        num_records (int): Number of synthetic traffic rows to generate.

    Returns:
        pd.DataFrame: Synthetic dataset dataframe.
    """
    records: List[Dict[str, Any]] = []
    
    countries = ["US", "DE", "CN", "RU", "NL", "JP", "BR", "GB"]
    asns = ["AS15169", "AS16509", "AS13335", "AS7018", "AS24940"]

    for _ in range(num_records):
        src_ip = fake.ipv4() if fake else f"192.168.1.{random.randint(1, 254)}"
        dst_ip = fake.ipv4() if fake else f"10.0.0.{random.randint(1, 254)}"
        
        # Sample bitcoin address stubs
        src_addr = f"1{random.randint(100000000000000000, 999999999999999999)}"
        dst_addr = f"3{random.randint(100000000000000000, 999999999999999999)}"
        
        records.append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": random.choice([8333, 8332, 18333, 49152, 50124]),
            "dst_port": 8333,
            "txid": f"{random.getrandbits(256):064x}",
            "input_addresses": src_addr,
            "output_addresses": dst_addr,
            "input_amounts": f"{round(random.uniform(0.01, 5.0), 8)}",
            "output_amounts": f"{round(random.uniform(0.01, 4.99), 8)}",
            "src_asn": random.choice(asns),
            "src_country": random.choice(countries),
            "dst_asn": random.choice(asns),
            "dst_country": random.choice(countries),
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Bitcoin traffic dataset")
    parser.add_argument("--output", type=str, default="../data/synthetic/sample_traffic.csv", help="Output file path")
    parser.add_argument("--count", type=int, default=500, help="Number of records to generate")
    args = parser.parse_args()

    print(f"Generating {args.count} synthetic records...")
    df_synthetic = generate_synthetic_dataset(args.count)
    df_synthetic.to_csv(args.output, index=False)
    print(f"Dataset saved to {args.output}")
