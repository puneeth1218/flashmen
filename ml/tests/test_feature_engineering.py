"""
Unit tests for the M3 Feature Engineering Pipeline (ml/feature_engineering.py).
Validates wallet-level aggregation, volume calculation, fan-in/fan-out ratios,
matrix shapes, data sanitization, and StandardScaler output.
"""

import numpy as np
import pandas as pd
import pytest
from ml.feature_engineering import extract_wallet_features, WALLET_FEATURE_COLUMNS


@pytest.fixture
def sample_tx_dataframe():
    """Provides a controlled synthetic DataFrame with known transaction flows."""
    records = [
        # Tx 1: wallet_A sends 2.0 BTC total (1.5 to wallet_B, 0.5 to wallet_C)
        {
            "txid": "tx01",
            "src_ip": "1.1.1.1",
            "dst_ip": "2.2.2.2",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": ["wallet_A"],
            "input_amounts": [2.0],
            "output_addresses": ["wallet_B", "wallet_C"],
            "output_amounts": [1.5, 0.5],
            "fee": 0.0,
            "script_type": "p2pkh",
        },
        # Tx 2: wallet_B sends 1.0 BTC to wallet_D
        {
            "txid": "tx02",
            "src_ip": "3.3.3.3",
            "dst_ip": "4.4.4.4",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": ["wallet_B"],
            "input_amounts": [1.0],
            "output_addresses": ["wallet_D"],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh",
        },
        # Tx 3: wallet_E sends 3.0 BTC (2.0 to wallet_A, 1.0 to wallet_F) from a distinct IP
        {
            "txid": "tx03",
            "src_ip": "5.5.5.5",
            "dst_ip": "6.6.6.6",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": ["wallet_E"],
            "input_amounts": [3.0],
            "output_addresses": ["wallet_A", "wallet_F"],
            "output_amounts": [2.0, 1.0],
            "fee": 0.0,
            "script_type": "p2pkh",
        },
    ]
    return pd.DataFrame(records)


def test_wallet_volume_aggregation(sample_tx_dataframe):
    """
    Validates correct calculation of inflow and outflow volumes and transaction counts.
    """
    raw_df, scaled = extract_wallet_features(sample_tx_dataframe)

    assert "wallet_A" in raw_df.index
    assert "wallet_B" in raw_df.index
    assert "wallet_C" in raw_df.index
    assert "wallet_D" in raw_df.index

    # Wallet A: Spent 2.0 in tx01, Received 2.0 in tx03, participated in 2 txs
    assert raw_df.loc["wallet_A", "total_volume_out"] == pytest.approx(2.0)
    assert raw_df.loc["wallet_A", "total_volume_in"] == pytest.approx(2.0)
    assert raw_df.loc["wallet_A", "tx_count"] == 2.0

    # Wallet B: Received 1.5 in tx01, Spent 1.0 in tx02, participated in 2 txs
    assert raw_df.loc["wallet_B", "total_volume_in"] == pytest.approx(1.5)
    assert raw_df.loc["wallet_B", "total_volume_out"] == pytest.approx(1.0)
    assert raw_df.loc["wallet_B", "tx_count"] == 2.0

    # Wallet C: Received 0.5 in tx01, Spent 0.0
    assert raw_df.loc["wallet_C", "total_volume_in"] == pytest.approx(0.5)
    assert raw_df.loc["wallet_C", "total_volume_out"] == pytest.approx(0.0)
    assert raw_df.loc["wallet_C", "tx_count"] == 1.0

    # Wallet D: Received 0.99 in tx02, Spent 0.0
    assert raw_df.loc["wallet_D", "total_volume_in"] == pytest.approx(0.99)
    assert raw_df.loc["wallet_D", "total_volume_out"] == pytest.approx(0.0)
    assert raw_df.loc["wallet_D", "tx_count"] == 1.0


def test_fan_in_and_fan_out_ratios():
    """
    Validates mathematical correctness of fan-in and fan-out ratios:
    - Peel chain pattern: 1 input -> 3 outputs (high fan-out)
    - Consolidation/mixer pattern: 4 inputs -> 1 output (high fan-in)
    """
    # 1. Peel chain transaction: 1 input, 3 outputs
    peel_df = pd.DataFrame([
        {
            "txid": "peel_tx",
            "src_ip": "1.2.3.4",
            "input_addresses": ["peel_sender"],
            "input_amounts": [10.0],
            "output_addresses": ["out1", "out2", "out3"],
            "output_amounts": [1.0, 2.0, 7.0],
        }
    ])
    raw_peel, _ = extract_wallet_features(peel_df)
    assert raw_peel.loc["peel_sender", "fan_out_ratio"] == pytest.approx(3.0 / 1.0)
    assert raw_peel.loc["peel_sender", "fan_in_ratio"] == pytest.approx(1.0 / 3.0)

    # 2. Consolidation transaction: 4 inputs, 1 output
    consolidation_df = pd.DataFrame([
        {
            "txid": "consolidate_tx",
            "src_ip": "5.6.7.8",
            "input_addresses": ["in1", "in2", "in3", "in4"],
            "input_amounts": [1.0, 1.0, 1.0, 1.0],
            "output_addresses": ["consolidated_target"],
            "output_amounts": [3.99],
        }
    ])
    raw_cons, _ = extract_wallet_features(consolidation_df)
    assert raw_cons.loc["consolidated_target", "fan_in_ratio"] == pytest.approx(4.0 / 1.0)
    assert raw_cons.loc["consolidated_target", "fan_out_ratio"] == pytest.approx(1.0 / 4.0)


def test_scaled_matrix_dimensions_and_no_nan_inf(sample_tx_dataframe):
    """
    Validates output matrix dimensions, column ordering, and confirms zero NaN or inf values.
    """
    raw_df, scaled_matrix = extract_wallet_features(sample_tx_dataframe)

    num_wallets = len(raw_df)
    num_features = len(WALLET_FEATURE_COLUMNS)

    assert num_wallets > 0
    assert num_features == 6
    assert list(raw_df.columns) == WALLET_FEATURE_COLUMNS

    # Check scaled matrix properties
    assert isinstance(scaled_matrix, np.ndarray)
    assert scaled_matrix.shape == (num_wallets, num_features)
    assert not np.isnan(scaled_matrix).any(), "Scaled matrix must not contain any NaN values"
    assert not np.isinf(scaled_matrix).any(), "Scaled matrix must not contain any infinite values"


def test_unique_ips_used():
    """
    Validates accurate distinct count of src_ip values associated with each wallet.
    """
    multi_ip_df = pd.DataFrame([
        {
            "txid": "txA",
            "src_ip": "10.0.0.1",
            "input_addresses": ["wallet_multi_ip"],
            "input_amounts": [1.0],
            "output_addresses": ["wallet_recv"],
            "output_amounts": [0.99],
        },
        {
            "txid": "txB",
            "src_ip": "10.0.0.2",
            "input_addresses": ["wallet_multi_ip"],
            "input_amounts": [2.0],
            "output_addresses": ["wallet_recv"],
            "output_amounts": [1.99],
        },
        {
            "txid": "txC",
            "src_ip": "10.0.0.1",  # Repeated IP
            "input_addresses": ["wallet_multi_ip"],
            "input_amounts": [0.5],
            "output_addresses": ["wallet_recv"],
            "output_amounts": [0.49],
        },
    ])

    raw_df, _ = extract_wallet_features(multi_ip_df)
    # wallet_multi_ip was observed on 10.0.0.1 and 10.0.0.2 -> 2 distinct IPs
    assert raw_df.loc["wallet_multi_ip", "unique_ips_used"] == 2.0


def test_empty_and_single_wallet_dataframe():
    """
    Validates edge cases: empty DataFrame and single-wallet DataFrame.
    """
    # Empty DataFrame
    empty_df = pd.DataFrame()
    raw_empty, scaled_empty = extract_wallet_features(empty_df)
    assert raw_empty.empty
    assert scaled_empty.shape == (0, 6)

    # Single-wallet DataFrame
    single_df = pd.DataFrame([
        {
            "txid": "tx_single",
            "src_ip": "8.8.8.8",
            "input_addresses": ["sole_wallet"],
            "input_amounts": [5.0],
            "output_addresses": ["sole_wallet"],
            "output_amounts": [4.99],
        }
    ])
    raw_single, scaled_single = extract_wallet_features(single_df)
    assert len(raw_single) == 1
    assert scaled_single.shape == (1, 6)
    assert not np.isnan(scaled_single).any()
    assert not np.isinf(scaled_single).any()
