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


def test_process_raw_file_with_dataframe():
    """Verifies that process_raw_file accepts a pre-loaded pandas DataFrame directly."""
    raw_df = pd.DataFrame([{
        "timestamp": "2026-03-31T12:00:00Z",
        "src_ip": "8.8.8.8",
        "dst_ip": "1.1.1.1",
        "src_port": 8333,
        "dst_port": 8333,
        "txid": "df_tx_01",
        "input_addresses": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,1CounterpartyXXXXXXXXXXXXXXXUWLpVr",
        "output_addresses": "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
        "input_amounts": "1.5, 0.5",
        "output_amounts": "1.99",
        "fee": 0.01,
        "script_type": "p2pkh"
    }])
    df = process_raw_file(raw_df)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df["input_addresses"].iloc[0] == ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "1CounterpartyXXXXXXXXXXXXXXXUWLpVr"]
    assert df["output_addresses"].iloc[0] == ["3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"]
    assert df["input_amounts"].iloc[0] == [1.5, 0.5]
    assert df["output_amounts"].iloc[0] == [1.99]


def test_api_ingest_csv_and_json(tmp_path):
    """Verifies that POST /api/v1/ingest accepts CSV, JSON, and nested formats seamlessly."""
    try:
        import inspect
        import httpx
        # Compatibility shim: In httpx >= 0.28.0, the deprecated 'app' parameter was removed
        # from httpx.Client.__init__. Starlette < 0.28.0 (used by FastAPI 0.100.0) still passes
        # app=self.app to super().__init__. Discard 'app' if httpx does not accept it.
        _orig_httpx_init = httpx.Client.__init__
        if "app" not in inspect.signature(_orig_httpx_init).parameters:
            def _patched_httpx_init(self, *args, **kwargs):
                kwargs.pop("app", None)
                return _orig_httpx_init(self, *args, **kwargs)
            httpx.Client.__init__ = _patched_httpx_init

        from fastapi.testclient import TestClient
    except (ModuleNotFoundError, ImportError):
        pytest.skip("httpx is required to run FastAPI TestClient")

    from backend.main import app

    client = TestClient(app)

    # 1. Test standard CSV upload
    csv_bytes = (
        b"timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n"
        b"2026-03-31T12:00:00Z,8.8.8.8,1.1.1.1,8333,8333,tx_api_01,112345678,312345678,1.0,0.99,0.01,p2pkh\n"
    )
    res_csv = client.post(
        "/api/v1/ingest",
        files={"file": ("sample.csv", csv_bytes, "text/csv")}
    )
    assert res_csv.status_code == 202, res_csv.text
    json_resp = res_csv.json()
    assert json_resp["status"] == "success"
    assert json_resp["processed_records"] == 1

    # 2. Test CSV upload with comma-separated list values (former Extra data error)
    csv_comma_bytes = (
        b"timestamp,src_ip,dst_ip,src_port,dst_port,txid,input_addresses,output_addresses,input_amounts,output_amounts,fee,script_type\n"
        b"2026-03-31T12:00:00Z,8.8.8.8,1.1.1.1,8333,8333,tx_comma_01,\"112345678,187654321\",\"312345678,387654321\",\"1.0,2.0\",\"0.9,1.9\",0.2,p2pkh\n"
    )
    res_csv_comma = client.post(
        "/api/v1/ingest",
        files={"file": ("sample_comma.csv", csv_comma_bytes, "text/csv")}
    )
    assert res_csv_comma.status_code == 202, res_csv_comma.text
    assert res_csv_comma.json()["status"] == "success"

    # 3. Test JSON list upload
    json_list_bytes = json.dumps([{
        "timestamp": "2026-03-31T12:00:00Z",
        "src_ip": "8.8.8.8",
        "dst_ip": "1.1.1.1",
        "src_port": 8333,
        "dst_port": 8333,
        "txid": "tx_json_01",
        "input_addresses": ["w_in_1"],
        "output_addresses": ["w_out_1"],
        "input_amounts": [1.0],
        "output_amounts": [0.99]
    }]).encode("utf-8")
    res_json = client.post(
        "/api/v1/ingest",
        files={"file": ("sample.json", json_list_bytes, "application/json")}
    )
    assert res_json.status_code == 202, res_json.text
    assert res_json.json()["processed_records"] == 1

    # 4. Test nested JSON (transactions key)
    nested_json_bytes = json.dumps({
        "transactions": [{
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            "dst_ip": "1.1.1.1",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "tx_nested_01",
            "input_addresses": ["w_in_nested"],
            "output_addresses": ["w_out_nested"],
            "input_amounts": [2.0],
            "output_amounts": [1.98]
        }]
    }).encode("utf-8")
    res_nested = client.post(
        "/api/v1/ingest",
        files={"file": ("nested.json", nested_json_bytes, "application/json")}
    )
    assert res_nested.status_code == 202, res_nested.text
    assert res_nested.json()["processed_records"] == 1

    # 5. Test JSONL (newline-delimited JSON)
    jsonl_bytes = (
        json.dumps({
            "timestamp": "2026-03-31T12:00:00Z",
            "src_ip": "8.8.8.8",
            "dst_ip": "1.1.1.1",
            "src_port": 8333,
            "dst_port": 8333,
            "txid": "tx_jsonl_01",
            "input_addresses": ["w_jsonl_1"],
            "output_addresses": ["w_jsonl_2"],
            "input_amounts": [3.0],
            "output_amounts": [2.95]
        }) + "\n"
    ).encode("utf-8")
    res_jsonl = client.post(
        "/api/v1/ingest",
        files={"file": ("stream.json", jsonl_bytes, "application/json")}
    )
    assert res_jsonl.status_code == 202, res_jsonl.text
    assert res_jsonl.json()["processed_records"] == 1

    # 6. Test Auto-detect fallback (filename without extension)
    res_fallback = client.post(
        "/api/v1/ingest",
        files={"file": ("raw_data_dump", csv_bytes, "application/octet-stream")}
    )
    assert res_fallback.status_code == 202, res_fallback.text
    assert res_fallback.json()["processed_records"] == 1