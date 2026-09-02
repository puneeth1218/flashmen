"""
Unit tests for feature engineering extraction pipeline.
"""

import pandas as pd
from ml.dataset_gen import generate_synthetic_dataset
from ml.feature_engineering import extract_features


def test_extract_features_schema():
    """
    Tests that feature extraction returns valid DataFrames for IPs and Wallets.
    """
    raw_df = generate_synthetic_dataset(num_records=10)
    ip_df, wallet_df = extract_features(raw_df)

    assert isinstance(ip_df, pd.DataFrame)
    assert isinstance(wallet_df, pd.DataFrame)
    
    if not ip_df.empty:
        assert "entity_id" in ip_df.columns
        assert "connection_count" in ip_df.columns
        assert "fan_out_ratio" in ip_df.columns

    if not wallet_df.empty:
        assert "entity_id" in wallet_df.columns
        assert "peel_chain_depth" in wallet_df.columns


def test_extract_features_empty_dataframe():
    """
    Tests handling of empty input DataFrame.
    """
    empty_df = pd.DataFrame()
    ip_df, wallet_df = extract_features(empty_df)
    assert ip_df.empty
    assert wallet_df.empty
