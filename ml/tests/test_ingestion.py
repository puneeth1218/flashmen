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
            "src_ip": "192.168.1.1",  # Private IP fallback test
            "dst_ip": "8.8.8.8",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "tx002",
            "input_addresses": ["wallet_B"],
            "output_addresses": ["wallet_D"],
            "input_amounts": [1.0],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        }
    ]
    file_path = tmp_path / "test_data.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_csv_file(tmp_path):
    """Creates a temporary valid CSV dataset with stringified array columns."""
    csv_content = (
        "timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n"
        '2026-03-31T12:00:00Z,8.8.8.8,1.1.1.1,8333,8333,tx_csv_01,"[""wallet_X""]","[""wallet_Y"", ""wallet_Z""]","[2.5]","[1.5, 0.99]",0.01,p2pkh\n'
        '2026-03-31T12:10:00Z,10.0.0.1,8.8.8.8,8333,8333,tx_csv_02,"[""wallet_Y""]","[""wallet_W""]","[1.5]","[1.48]",0.02,p2wpkh\n'
    )
    file_path = tmp_path / "test_data.csv"
    file_path.write_text(csv_content, encoding="utf-8")
    return str(file_path)


def test_process_raw_file_json(sample_json_file):
    """Verifies that process_raw_file parses JSON and returns expected structure."""
    df = process_raw_file(sample_json_file)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "src_country" in df.columns
    assert "dst_country" in df.columns
    assert df["txid"].tolist() == ["tx001", "tx002"]
    
    # Assert proper list deserialization
    assert isinstance(df["input_addresses"].iloc[0], list)
    assert isinstance(df["output_addresses"].iloc[0], list)
    assert isinstance(df["input_amounts"].iloc[0], list)
    assert isinstance(df["output_amounts"].iloc[0], list)
    assert df["input_addresses"].iloc[0] == ["wallet_A"]
    assert df["output_addresses"].iloc[0] == ["wallet_B", "wallet_C"]
    assert df["input_amounts"].iloc[0] == [1.5]
    assert df["output_amounts"].iloc[0] == [1.0, 0.49]

    # Assert UTC timestamp parsing
    assert isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype)
    assert str(df["timestamp"].dt.tz) in ("UTC", "datetime.timezone.utc")

    # Assert GeoIP enrichment with offline database / fallback
    assert df["src_country"].iloc[0] == "US"
    assert df["src_country"].iloc[1] == "UNKNOWN"


def test_process_raw_file_csv(sample_csv_file):
    """Verifies that process_raw_file parses CSV with stringified lists and normalizes schema."""
    df = process_raw_file(sample_csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "src_country" in df.columns
    assert "dst_country" in df.columns
    assert df["txid"].tolist() == ["tx_csv_01", "tx_csv_02"]

    # Verify stringified JSON array deserialization into real Python lists
    assert isinstance(df["input_addresses"].iloc[0], list)
    assert isinstance(df["output_addresses"].iloc[0], list)
    assert isinstance(df["input_amounts"].iloc[0], list)
    assert isinstance(df["output_amounts"].iloc[0], list)
    assert df["input_addresses"].iloc[0] == ["wallet_X"]
    assert df["output_addresses"].iloc[0] == ["wallet_Y", "wallet_Z"]
    assert df["input_amounts"].iloc[0] == [2.5]
    assert df["output_amounts"].iloc[0] == [1.5, 0.99]

    # Verify UTC timestamp parsing
    assert isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype)
    assert str(df["timestamp"].dt.tz) in ("UTC", "datetime.timezone.utc")

    # Verify GeoIP resolution
    assert df["src_country"].iloc[0] == "US"
    assert df["src_country"].iloc[1] == "UNKNOWN"


def test_invalid_data_dropping(tmp_path):
    """Verifies that invalid rows are filtered out and ValueError raised when no valid rows remain."""
    # File with only invalid row
    all_invalid = [
        {
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            # Missing required fields: txid, input_addresses, etc.
        }
    ]
    file_path = tmp_path / "all_invalid.json"
    file_path.write_text(json.dumps(all_invalid), encoding="utf-8")
    
    with pytest.raises(ValueError, match="No valid records found"):
        process_raw_file(str(file_path))

    # File with mixed valid and invalid rows
    mixed_data = [
        {
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            "dst_ip": "1.1.1.1",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "valid_tx",
            "input_addresses": ["w1"],
            "output_addresses": ["w2"],
            "input_amounts": [1.0],
            "output_amounts": [0.99]
        },
        {
            "timestamp": "invalid_timestamp",
            "src_ip": "8.8.8.8"
            # Missing other fields
        }
    ]
    mixed_path = tmp_path / "mixed.json"
    mixed_path.write_text(json.dumps(mixed_data), encoding="utf-8")
    df = process_raw_file(str(mixed_path))
    assert len(df) == 1
    assert df["txid"].iloc[0] == "valid_tx"