"""
Faker-based Synthetic Bitcoin Traffic Dataset Generator.
Generates test datasets with realistic IP addresses, ASN numbers, GeoIP data,
and Bitcoin transactions (benign, peel chains, fan-out, and mixer/consolidation).
"""

import argparse
import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    fake = None


def _random_btc_address(prefix_choice: str = None) -> str:
    """Generates a realistic synthetic Bitcoin address string."""
    choice = prefix_choice or random.choice(["legacy", "p2sh", "bech32"])
    if choice == "legacy":
        charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return "1" + "".join(random.choices(charset, k=33))
    elif choice == "p2sh":
        charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return "3" + "".join(random.choices(charset, k=33))
    else:
        charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
        return "bc1q" + "".join(random.choices(charset, k=38))


def generate_synthetic_dataset(num_records: int = 500, seed: int = None) -> pd.DataFrame:
    """
    Generates a diverse synthetic Bitcoin transaction DataFrame.

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

    countries = ["US", "DE", "CN", "RU", "NL", "JP", "BR", "GB", "CH", "SG"]
    asns = ["AS15169", "AS16509", "AS13335", "AS7018", "AS24940", "AS8075", "AS16276"]
    script_types = ["p2pkh", "p2wpkh", "p2sh"]

    # Pre-generate recurring core addresses to ensure realistic graph topology and entity clustering
    pool_size = max(30, num_records // 6)
    address_pool = [_random_btc_address() for _ in range(pool_size)]
    ip_pool = [fake.ipv4() if fake else f"192.168.1.{random.randint(1, 254)}" for _ in range(pool_size // 2)]

    # Persistent wallet for peel chain generation
    peel_wallet = _random_btc_address("legacy")
    peel_balance = 25.0

    # Start timestamp staggered across hours
    base_timestamp = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=num_records * 3)

    for i in range(num_records):
        # 70% benign, 12% peel chain, 10% mixer/consolidation, 8% fan-out
        roll = random.random()
        if roll < 0.70:
            pattern_type = "benign"
        elif roll < 0.82:
            pattern_type = "peel_chain"
        elif roll < 0.92:
            pattern_type = "mixer"
        else:
            pattern_type = "fan_out"

        src_ip = random.choice(ip_pool) if random.random() < 0.6 else (fake.ipv4() if fake else f"10.0.0.{random.randint(1, 254)}")
        dst_ip = fake.ipv4() if fake else f"172.16.0.{random.randint(1, 254)}"
        src_port = random.choice([8333, 8332, 18333, 49152, 50124, 52140])
        dst_port = 8333
        tx_time = base_timestamp + pd.Timedelta(seconds=i * random.randint(45, 180))

        fee = round(random.uniform(0.0001, 0.0008), 8)
        script_type = random.choice(script_types)

        if pattern_type == "peel_chain":
            # Peel chain: 1 input peeling a small amount to recipient and large change to new/peeled address
            src_addr = peel_wallet
            peel_amt = round(random.uniform(0.05, 0.45), 8)
            peel_wallet = _random_btc_address("legacy")  # change address peels forward
            dst_addrs = [random.choice(address_pool), peel_wallet]
            peel_balance = max(0.5, round(peel_balance - peel_amt - fee, 8))
            
            input_amounts = [round(peel_balance + peel_amt + fee, 8)]
            output_amounts = [peel_amt, peel_balance]
            src_addrs_str = src_addr
            dst_addrs_str = ",".join(dst_addrs)
            in_amt_str = str(input_amounts[0])
            out_amt_str = ",".join(str(a) for a in output_amounts)

        elif pattern_type == "mixer":
            # Mixer/consolidation: multiple inputs merging into 1 or 2 outputs
            num_inputs = random.randint(3, 6)
            in_wallets = random.sample(address_pool, k=min(num_inputs, len(address_pool)))
            out_wallets = [_random_btc_address() for _ in range(random.choice([1, 2]))]
            
            in_amounts = [round(random.uniform(0.2, 1.5), 8) for _ in in_wallets]
            tot_in = sum(in_amounts)
            tot_out = tot_in - fee
            if len(out_wallets) == 1:
                out_amounts = [round(tot_out, 8)]
            else:
                s1 = round(tot_out * 0.5, 8)
                out_amounts = [s1, round(tot_out - s1, 8)]

            src_addrs_str = ",".join(in_wallets)
            dst_addrs_str = ",".join(out_wallets)
            in_amt_str = ",".join(str(a) for a in in_amounts)
            out_amt_str = ",".join(str(a) for a in out_amounts)

        elif pattern_type == "fan_out":
            # Fan-out: single input distributing to 4 to 8 outputs
            num_outputs = random.randint(4, 7)
            src_addr = random.choice(address_pool)
            out_wallets = [_random_btc_address() for _ in range(num_outputs)]
            
            tot_in = round(random.uniform(1.0, 5.0), 8)
            split_amt = round((tot_in - fee) / num_outputs, 8)
            out_amounts = [split_amt] * (num_outputs - 1)
            out_amounts.append(round((tot_in - fee) - sum(out_amounts), 8))

            src_addrs_str = src_addr
            dst_addrs_str = ",".join(out_wallets)
            in_amt_str = str(tot_in)
            out_amt_str = ",".join(str(a) for a in out_amounts)

        else:
            # Benign: 1 input, 1 or 2 outputs
            src_addr = random.choice(address_pool)
            if random.random() < 0.4:
                # 1-to-1 payment
                dst_addr = random.choice(address_pool)
                amt = round(random.uniform(0.01, 1.2), 8)
                src_addrs_str = src_addr
                dst_addrs_str = dst_addr
                in_amt_str = str(round(amt + fee, 8))
                out_amt_str = str(amt)
            else:
                # 1-to-2 payment + change
                dst_recipient = random.choice(address_pool)
                dst_change = _random_btc_address()
                pay_amt = round(random.uniform(0.01, 0.8), 8)
                change_amt = round(random.uniform(0.05, 1.5), 8)
                src_addrs_str = src_addr
                dst_addrs_str = f"{dst_recipient},{dst_change}"
                in_amt_str = str(round(pay_amt + change_amt + fee, 8))
                out_amt_str = f"{pay_amt},{change_amt}"

        records.append({
            "timestamp": tx_time.isoformat(),
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "txid": f"{random.getrandbits(256):064x}",
            "input_addresses": src_addrs_str,
            "output_addresses": dst_addrs_str,
            "input_amounts": in_amt_str,
            "output_amounts": out_amt_str,
            "fee": fee,
            "script_type": script_type,
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
    parser.add_argument("--output", type=str, default="data/synthetic/sample_500.csv", help="Output file path")
    parser.add_argument("--rows", type=int, default=500, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.rows} synthetic records with seed {args.seed}...")
    df_synthetic = generate_synthetic_dataset(args.rows, args.seed)
    df_synthetic.to_csv(output_path, index=False)
    print(f"Dataset saved to {output_path} ({len(df_synthetic)} rows)")
