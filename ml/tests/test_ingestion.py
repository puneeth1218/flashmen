
import json
import pytest
import pandas as pd
from backend.services.ingestion import process_raw_file

@pytest.fixture
def sample_json_file(tmp_path):
    """Creates a temporary valid JSON dataset with 2 transactions."""
    data = [
        {
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            "dst_ip": "1.1.1.1",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "tx001",
            "input_addresses": ["wallet_A"],
            "output_addresses": ["wallet_B", "wallet_C"],
            "input_amounts": [1.5],
            "output_amounts": [1.0, 0.49],
            "fee": 0.01,
            "script_type": "p2pkh"
        },
        {
            "timestamp": "2026-03-31T12:05:00Z",
            "src_ip": "192.168.1.1", # Private IP fallback test
            "dst_ip": "8.8.8.8",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "tx002",
            "input_addresses": ["wallet_B"],
            "output_addresses": ["wallet_D"],
            "input_amounts": [1.0],
            "output_amounts": [0.99],
            "fee": 0.01
        }
    ]
    file_path = tmp_path / "test_data.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return str(file_path)


def test_process_raw_file_json(sample_json_file):
    """Verifies that process_raw_file parses JSON and returns expected structure."""
    df = process_raw_file(sample_json_file)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "src_country" in df.columns
    assert "dst_country" in df.columns
    assert df["txid"].tolist() == ["tx001", "tx002"]
    assert isinstance(df["input_addresses"].iloc[0], list)


def test_invalid_data_dropping(tmp_path):
    """Verifies that invalid rows (missing required fields) are filtered out."""
    data = [
        {
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            # Missing txid and input_addresses
        }
    ]
    file_path = tmp_path / "invalid_data.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    
    with pytest.raises(ValueError, match="No valid records found"):
        process_raw_file(str(file_path))