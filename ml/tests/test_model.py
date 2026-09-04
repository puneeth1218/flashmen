"""
Unit tests for Module M3 Model Training, Risk Scoring Engine & Explainability (ml/model.py).
Validates IsolationForest model training, inference on DataFrame and NumPy matrices,
0–100 risk score calibration, outlier discrimination, and human-readable anomaly attribution.
"""

import numpy as np
import pandas as pd
import pytest
from ml.model import (
    IsolationForestAnomalyDetector,
    INVESTIGATIVE_TAG_MAPPING,
    get_investigative_tag
)
from ml.explainer import ShapExplainer
from ml.feature_engineering import extract_wallet_features, WALLET_FEATURE_COLUMNS


def test_isolation_forest_fit_predict():
    """
    Tests fitting and score calculations on IsolationForest wrapper with DataFrame input.
    """
    detector = IsolationForestAnomalyDetector(contamination=0.1, random_state=42)

    # Create sample numerical dataframe
    X = pd.DataFrame({
        "feature1": np.random.normal(0, 1, 50),
        "feature2": np.random.normal(5, 2, 50)
    })

    detector.fit(X)
    assert detector.is_fitted
    assert detector.feature_names == ["feature1", "feature2"]

    predictions = detector.predict(X)
    assert len(predictions) == 50
    assert set(predictions).issubset({-1, 1})

    scores = detector.score_samples(X)
    assert len(scores) == 50
    assert (scores >= 0.0).all() and (scores <= 100.0).all()


def test_isolation_forest_numpy_array_input():
    """
    Validates that IsolationForestAnomalyDetector seamlessly accepts 2D NumPy array matrices
    such as those output by extract_wallet_features()[1].
    """
    np.random.seed(42)
    mock_scaled_matrix = np.random.normal(0, 1, size=(60, 6))

    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(mock_scaled_matrix)

    assert detector.is_fitted
    assert detector.feature_names == WALLET_FEATURE_COLUMNS

    preds = detector.predict(mock_scaled_matrix)
    assert preds.shape == (60,)
    assert set(preds).issubset({-1, 1})

    scores = detector.score_samples(mock_scaled_matrix)
    assert scores.shape == (60,)
    assert (scores >= 0.0).all() and (scores <= 100.0).all()


def test_risk_score_bounds_and_calibration():
    """
    Validates that risk scores are strictly bounded in [0.0, 100.0] under normal,
    extreme outlier, and edge-case inputs.
    """
    np.random.seed(42)
    train_data = np.random.normal(0, 1, size=(100, 4))
    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(train_data)

    # 1. Normal inference data
    normal_test = np.random.normal(0, 1, size=(20, 4))
    normal_scores = detector.score_samples(normal_test)
    assert (normal_scores >= 0.0).all() and (normal_scores <= 100.0).all()

    # 2. Extreme outlier data (far away from normal distribution)
    outlier_test = np.array([
        [100.0, 200.0, 300.0, 400.0],
        [-50.0, -80.0, -120.0, -200.0]
    ])
    outlier_scores = detector.score_samples(outlier_test)
    assert (outlier_scores >= 0.0).all() and (outlier_scores <= 100.0).all()
    # Outliers must receive high risk scores (> 70.0)
    assert (outlier_scores > 70.0).all()

    # 3. Single instance scoring
    single_score = detector.score_samples(normal_test[0])
    assert len(single_score) == 1
    assert 0.0 <= single_score[0] <= 100.0

    # 4. Unfitted error handling
    unfitted_detector = IsolationForestAnomalyDetector()
    with pytest.raises(ValueError, match="not fitted yet"):
        unfitted_detector.predict(normal_test)

    with pytest.raises(ValueError, match="not fitted yet"):
        unfitted_detector.score_samples(normal_test)


def test_synthetic_outlier_wallets_score_significantly_higher():
    """
    Tests that synthetic anomalous wallets (extreme peel-chain fan-out and multi-IP sybil relay)
    score significantly higher than standard 1-to-1 normal wallets.
    """
    records = []

    # 1. Create 50 standard 1-to-1 transactions
    for i in range(50):
        records.append({
            "txid": f"std_tx_{i:03d}",
            "src_ip": f"192.168.1.{(i % 5) + 1}",
            "dst_ip": "192.168.1.200",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": [f"wallet_norm_{i}"],
            "input_amounts": [1.0],
            "output_addresses": [f"wallet_dest_{i}"],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        })

    # 2. Add Peel Chain Outlier: 1 input splitting into 30 outputs (extreme fan-out)
    records.append({
        "txid": "tx_peel_chain_outlier",
        "src_ip": "10.0.0.50",
        "dst_ip": "192.168.1.200",
        "src_port": 8333,
        "dst_port": 8333,
        "input_addresses": ["wallet_peel_outlier"],
        "input_amounts": [50.0],
        "output_addresses": [f"split_dest_{k}" for k in range(30)],
        "output_amounts": [1.5] * 30,
        "fee": 0.05,
        "script_type": "p2pkh"
    })

    # 3. Add Sybil / Multi-IP Broadcaster: single wallet broadcasting from 15 distinct IPs
    for ip_idx in range(15):
        records.append({
            "txid": f"tx_sybil_{ip_idx:02d}",
            "src_ip": f"203.0.113.{ip_idx + 1}",
            "dst_ip": "192.168.1.200",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": ["wallet_sybil_outlier"],
            "input_amounts": [2.0],
            "output_addresses": [f"sybil_dest_{ip_idx}"],
            "output_amounts": [1.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        })

    tx_df = pd.DataFrame(records)
    raw_wallet_df, scaled_matrix = extract_wallet_features(tx_df)

    # Train detector on scaled wallet features
    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(scaled_matrix)

    # Generate calibrated 0-100 risk scores
    risk_scores = detector.score_samples(scaled_matrix)
    raw_wallet_df["risk_score"] = risk_scores

    peel_score = float(raw_wallet_df.loc["wallet_peel_outlier", "risk_score"])
    sybil_score = float(raw_wallet_df.loc["wallet_sybil_outlier", "risk_score"])

    # Sample normal sender wallets
    normal_wallet_ids = [f"wallet_norm_{i}" for i in range(20)]
    normal_scores = raw_wallet_df.loc[normal_wallet_ids, "risk_score"]
    normal_avg = float(normal_scores.mean())
    normal_max = float(normal_scores.max())

    # Assertions: Outliers must score significantly higher than standard wallets
    assert peel_score >= 80.0, f"Expected peel chain score >= 80.0, got {peel_score}"
    assert sybil_score >= 80.0, f"Expected sybil score >= 80.0, got {sybil_score}"
    assert normal_avg <= 20.0, f"Expected normal wallet average score <= 20.0, got {normal_avg}"
    assert (peel_score - normal_max) >= 40.0, "Peel outlier risk score must be significantly higher than standard wallets"
    assert (sybil_score - normal_max) >= 40.0, "Sybil outlier risk score must be significantly higher than standard wallets"


def test_signal_breakdown_attribution():
    """
    Validates that explain_instance and get_signal_breakdown identify the dominant
    features driving the anomaly classification.
    """
    records = []
    # Normal background traffic
    for i in range(40):
        records.append({
            "txid": f"tx_bg_{i}",
            "src_ip": "192.168.1.1",
            "dst_ip": "192.168.1.2",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": [f"wallet_bg_{i}"],
            "input_amounts": [1.0],
            "output_addresses": [f"wallet_recv_{i}"],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        })

    # High fan-out peel chain
    records.append({
        "txid": "tx_peel_signal",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "src_port": 8333,
        "dst_port": 8333,
        "input_addresses": ["wallet_peel_subject"],
        "input_amounts": [100.0],
        "output_addresses": [f"peel_out_{k}" for k in range(25)],
        "output_amounts": [3.9] * 25,
        "fee": 0.1,
        "script_type": "p2pkh"
    })

    # High unique IP sybil wallet
    for ip_idx in range(12):
        records.append({
            "txid": f"tx_multi_{ip_idx}",
            "src_ip": f"172.16.0.{ip_idx + 1}",
            "dst_ip": "10.0.0.2",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": ["wallet_sybil_subject"],
            "input_amounts": [1.0],
            "output_addresses": [f"multi_recv_{ip_idx}"],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        })

    df = pd.DataFrame(records)
    raw_wallet_df, scaled_matrix = extract_wallet_features(df)

    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(raw_wallet_df)

    # 1. Test explain_instance on peel chain wallet
    peel_explanation = detector.explain_instance(raw_wallet_df.loc["wallet_peel_subject"])
    assert isinstance(peel_explanation, dict)
    assert set(peel_explanation.keys()) == set(WALLET_FEATURE_COLUMNS)
    assert pytest.approx(sum(peel_explanation.values()), abs=1e-3) == 1.0
    # Peel chain outlier has high fan_out_ratio and total_volume_out
    assert peel_explanation["fan_out_ratio"] > 0.05
    assert peel_explanation["total_volume_out"] > 0.05

    # 2. Test get_signal_breakdown with top_n
    top_peel = detector.get_signal_breakdown(raw_wallet_df.loc["wallet_peel_subject"], top_n=2)
    assert len(top_peel) == 2
    # Ensure items are ordered descending
    values = list(top_peel.values())
    assert values[0] >= values[1]

    # 3. Test sybil multi-IP wallet explanation
    sybil_explanation = detector.explain_instance(raw_wallet_df.loc["wallet_sybil_subject"])
    assert isinstance(sybil_explanation, dict)
    # For sybil wallet, unique_ips_used and tx_count are dominant
    top_sybil_keys = list(detector.get_signal_breakdown(raw_wallet_df.loc["wallet_sybil_subject"], top_n=2).keys())
    assert "unique_ips_used" in top_sybil_keys or "tx_count" in top_sybil_keys


def test_anomalous_wallets_return_top_risk_factors():
    """
    Verifies that wallets flagged as anomalous return a non-empty list of human-readable
    top risk factors, and that score_and_explain attaches all explainability metadata.
    """
    records = []
    # 30 Normal transactions
    for i in range(30):
        records.append({
            "txid": f"normal_tx_{i}",
            "src_ip": "192.168.1.1",
            "dst_ip": "192.168.1.10",
            "src_port": 8333,
            "dst_port": 8333,
            "input_addresses": [f"norm_w_{i}"],
            "input_amounts": [1.0],
            "output_addresses": [f"recv_w_{i}"],
            "output_amounts": [0.99],
            "fee": 0.01,
            "script_type": "p2pkh"
        })

    # Injected peel chain anomaly
    records.append({
        "txid": "anomaly_peel",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "src_port": 8333,
        "dst_port": 8333,
        "input_addresses": ["flagged_peel_wallet"],
        "input_amounts": [80.0],
        "output_addresses": [f"peel_dst_{k}" for k in range(25)],
        "output_amounts": [3.1] * 25,
        "fee": 0.05,
        "script_type": "p2pkh"
    })

    df = pd.DataFrame(records)
    raw_wallet_df, _ = extract_wallet_features(df)

    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(raw_wallet_df)

    scored_df = detector.score_and_explain(raw_wallet_df, anomaly_threshold=60.0, top_n=3)

    # Validate output schema
    assert "risk_score" in scored_df.columns
    assert "is_anomaly" in scored_df.columns
    assert "top_risk_factors" in scored_df.columns
    assert "top_features" in scored_df.columns
    assert "signal_breakdown" in scored_df.columns
    assert "reason" in scored_df.columns

    # Validate anomalous wallet explainability
    peel_row = scored_df.loc["flagged_peel_wallet"]
    assert peel_row["is_anomaly"] is True or peel_row["is_anomaly"] == 1
    assert peel_row["risk_score"] >= 60.0

    risk_factors = peel_row["top_risk_factors"]
    assert isinstance(risk_factors, list)
    assert len(risk_factors) > 0, "Flagged anomalous wallet must return a non-empty list of top risk factors"

    # Confirm expected peel-chain tag is present in top risk factors
    peel_tag = INVESTIGATIVE_TAG_MAPPING["fan_out_ratio"]
    assert peel_tag in risk_factors or INVESTIGATIVE_TAG_MAPPING["total_volume_out"] in risk_factors

    # Confirm reason string format starts directly without redundant prefix
    assert not peel_row["reason"].startswith("Flagged due to:")
    assert any(tag in peel_row["reason"] for tag in risk_factors)


def test_injected_extreme_feature_attribution():
    """
    Verifies that a wallet with an artificially injected extreme feature (e.g. 50 unique IPs)
    correctly isolates and attributes that specific feature as the top contributing factor.
    """
    np.random.seed(42)
    # Baseline population: 60 normal wallets with ~1 unique IP, small volume
    baseline_rows = []
    for i in range(60):
        baseline_rows.append({
            "tx_count": float(np.random.randint(1, 4)),
            "total_volume_in": float(np.random.uniform(0.5, 3.0)),
            "total_volume_out": float(np.random.uniform(0.5, 3.0)),
            "fan_out_ratio": float(np.random.uniform(0.8, 1.2)),
            "fan_in_ratio": float(np.random.uniform(0.8, 1.2)),
            "unique_ips_used": 1.0,
        })
    baseline_df = pd.DataFrame(baseline_rows)

    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(baseline_df)

    # Injected wallet with 50 unique IPs (extreme sybil broadcast)
    sybil_wallet = pd.Series({
        "tx_count": 2.0,
        "total_volume_in": 1.0,
        "total_volume_out": 1.0,
        "fan_out_ratio": 1.0,
        "fan_in_ratio": 1.0,
        "unique_ips_used": 50.0,
    })

    top_factors = detector.get_top_factors(sybil_wallet, top_n=3)
    assert len(top_factors) == 3
    top_feature_name, top_tag, top_weight = top_factors[0]

    assert top_feature_name == "unique_ips_used", f"Expected unique_ips_used as top factor, got {top_feature_name}"
    assert top_tag == "Rapid Multi-IP Broadcast"
    assert top_weight > 0.85, f"Expected dominant weight > 0.85, got {top_weight}"

    tags = detector.get_investigative_tags(sybil_wallet, top_n=2)
    assert tags[0] == "Rapid Multi-IP Broadcast"

    reason = detector.get_anomaly_reason(sybil_wallet)
    assert "Rapid Multi-IP Broadcast" in reason


def test_attribution_edge_cases_zero_variance_and_uniform():
    """
    Verifies that explain_instance and score_and_explain handle zero-variance features
    and uniform datasets cleanly without ZeroDivisionError or NaN/inf values.
    """
    # 1. Zero-variance feature test (fan_out_ratio is constant 1.0 across all training data)
    data = np.random.normal(loc=[2, 1.0, 1.0, 1.0, 1.0, 1.0], scale=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1], size=(40, 6))
    data[:, 3] = 1.0  # fan_out_ratio has zero variance
    df_zero_var = pd.DataFrame(data, columns=WALLET_FEATURE_COLUMNS)

    detector = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector.fit(df_zero_var)

    # Test sample with normal value on zero-var feature
    normal_sample = pd.Series({
        "tx_count": 2.0, "total_volume_in": 1.0, "total_volume_out": 1.0,
        "fan_out_ratio": 1.0, "fan_in_ratio": 1.0, "unique_ips_used": 1.0
    })
    exp_norm = detector.explain_instance(normal_sample)
    assert isinstance(exp_norm, dict)
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_norm.values())
    assert pytest.approx(sum(exp_norm.values()), abs=1e-3) == 1.0

    # Test sample with outlier value on the zero-variance feature
    outlier_sample = pd.Series({
        "tx_count": 2.0, "total_volume_in": 1.0, "total_volume_out": 1.0,
        "fan_out_ratio": 50.0, "fan_in_ratio": 1.0, "unique_ips_used": 1.0
    })
    exp_out = detector.explain_instance(outlier_sample)
    assert isinstance(exp_out, dict)
    assert exp_out["fan_out_ratio"] > 0.80
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_out.values())

    # 2. Completely uniform dataset test (all samples identical)
    uniform_matrix = np.ones((30, 6), dtype=float)
    detector_uniform = IsolationForestAnomalyDetector(contamination=0.02, random_state=42)
    detector_uniform.fit(uniform_matrix)

    exp_uniform = detector_uniform.explain_instance(uniform_matrix[0])
    assert isinstance(exp_uniform, dict)
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_uniform.values())
    assert pytest.approx(sum(exp_uniform.values()), abs=1e-3) == 1.0
    # All features share equal attribution
    assert all(pytest.approx(v, abs=1e-3) == (1.0 / 6) for v in exp_uniform.values())

    scored_uniform = detector_uniform.score_and_explain(uniform_matrix)
    assert len(scored_uniform) == 30
    assert not scored_uniform["risk_score"].isna().any()


def test_shap_explainer():
    """
    Tests SHAP explainer attribution output structure and fallback capability.
    """
    explainer = ShapExplainer()
    sample_series = pd.Series({"feature1": 1.5, "feature2": 4.2})
    explanation = explainer.explain_instance(sample_series)

    assert isinstance(explanation, dict)
    assert "feature1" in explanation
    assert "feature2" in explanation
    assert pytest.approx(sum(explanation.values()), abs=1e-3) == 1.0
    assert sum(explanation.values()) == 1.0


def test_shap_explainer_synthetic_outlier_attribution():
    """
    Verifies that ShapExplainer integrated with shap.TreeExplainer computes true
    local Shapley attribution values from a trained IsolationForest:
    - Returns non-zero, genuine Shapley values on synthetic outlier inputs.
    - Feature attributions sum strictly to 1.0 (100%).
    - Top SHAP-identified features accurately reflect ground-truth synthetic drivers:
      * fan_out_ratio for peel chain pattern
      * unique_ips_used for multi-IP broadcast pattern
    - Human-readable forensic tags and anomaly reason strings match established taxonomy.
    """
    np.random.seed(42)
    baseline_rows = []
    for i in range(120):
        baseline_rows.append({
            "tx_count": float(np.random.randint(1, 10)),
            "total_volume_in": float(np.random.uniform(500.0, 5000.0)),
            "total_volume_out": float(np.random.uniform(500.0, 5000.0)),
            "fan_out_ratio": float(np.random.uniform(0.1, 0.4)),
            "fan_in_ratio": float(np.random.uniform(0.1, 0.4)),
            "unique_ips_used": float(np.random.choice([1, 2, 3])),
        })
    df_base = pd.DataFrame(baseline_rows)

    detector = IsolationForestAnomalyDetector(contamination=0.03, random_state=42)
    detector.fit(df_base)

    explainer = ShapExplainer(detector)

    # 1. Peel chain outlier verification
    peel_outlier = pd.Series({
        "tx_count": 3.0,
        "total_volume_in": 1000.0,
        "total_volume_out": 1000.0,
        "fan_out_ratio": 25.0,
        "fan_in_ratio": 0.2,
        "unique_ips_used": 1.0,
    })

    exp_peel = explainer.explain_instance(peel_outlier)
    assert isinstance(exp_peel, dict)
    assert len(exp_peel) == len(detector.feature_names)
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_peel.values())
    assert all(v >= 0.0 for v in exp_peel.values()), "Expected genuine non-negative Shapley attributions"
    assert any(v > 0.0 for v in exp_peel.values())
    assert pytest.approx(sum(exp_peel.values()), abs=1e-3) == 1.0

    # fan_out_ratio must be top contributing feature
    top_peel_feature = max(exp_peel, key=exp_peel.get)
    assert top_peel_feature == "fan_out_ratio", f"Expected fan_out_ratio to dominate, got {top_peel_feature}"
    assert exp_peel["fan_out_ratio"] > 0.35

    # Verify forensic tags and reason
    peel_factors = explainer.get_top_factors(peel_outlier, top_n=2)
    assert peel_factors[0][0] == "fan_out_ratio"
    assert peel_factors[0][1] == "High Fan-Out (Peel Chain Pattern)"

    peel_tags = explainer.get_investigative_tags(peel_outlier, top_n=2)
    assert peel_tags[0] == "High Fan-Out (Peel Chain Pattern)"
    peel_reason = explainer.get_anomaly_reason(peel_outlier)
    assert "High Fan-Out (Peel Chain Pattern)" in peel_reason

    # 2. Multi-IP broadcast outlier verification
    sybil_outlier = pd.Series({
        "tx_count": 4.0,
        "total_volume_in": 1000.0,
        "total_volume_out": 1000.0,
        "fan_out_ratio": 0.25,
        "fan_in_ratio": 0.25,
        "unique_ips_used": 50.0,
    })

    exp_sybil = explainer.explain_instance(sybil_outlier)
    assert isinstance(exp_sybil, dict)
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_sybil.values())
    assert all(v >= 0.0 for v in exp_sybil.values())
    assert any(v > 0.0 for v in exp_sybil.values())
    assert pytest.approx(sum(exp_sybil.values()), abs=1e-3) == 1.0

    # unique_ips_used must be top contributing feature
    top_sybil_feature = max(exp_sybil, key=exp_sybil.get)
    assert top_sybil_feature == "unique_ips_used", f"Expected unique_ips_used to dominate, got {top_sybil_feature}"
    assert exp_sybil["unique_ips_used"] > 0.20

    sybil_tags = explainer.get_investigative_tags(sybil_outlier, top_n=2)
    assert sybil_tags[0] == "Rapid Multi-IP Broadcast"
    sybil_reason = explainer.get_anomaly_reason(sybil_outlier)
    assert "Rapid Multi-IP Broadcast" in sybil_reason


def test_shap_explainer_edge_cases_and_matrix_inputs():
    """
    Tests ShapExplainer with raw sklearn IsolationForest, NumPy matrix inputs,
    zero-variance datasets, and batch dataset explanation.
    """
    from sklearn.ensemble import IsolationForest as SklearnIF

    np.random.seed(42)
    X_train = np.random.normal(loc=0.0, scale=1.0, size=(80, 5))
    raw_clf = SklearnIF(n_estimators=40, random_state=42)
    raw_clf.fit(X_train)

    feat_names = ["feat_a", "feat_b", "feat_c", "feat_d", "feat_e"]
    explainer = ShapExplainer(raw_clf, feature_names=feat_names)

    # 1. 1D NumPy array input
    row_1d = np.array([0.1, 0.2, 0.3, 0.4, 10.0])
    exp_1d = explainer.explain_instance(row_1d)

    assert isinstance(exp_1d, dict)
    assert len(exp_1d) == 5
    assert pytest.approx(sum(exp_1d.values()), abs=1e-3) == 1.0
    assert all(v >= 0.0 for v in exp_1d.values())
    assert any(v > 0.0 for v in exp_1d.values())

    # 2. 2D NumPy array input (single row)
    row_2d = row_1d.reshape(1, -1)
    exp_2d = explainer.explain_instance(row_2d)
    assert exp_2d == exp_1d

    # 3. Raw SHAP matrix extraction
    shap_mat, names = explainer.get_shap_matrix(row_2d)
    assert shap_mat.shape == (1, 5)
    assert names == feat_names

    # 4. Batch explain_dataset
    batch_X = np.random.normal(loc=0.0, scale=1.0, size=(10, 5))
    batch_exps = explainer.explain_dataset(batch_X)
    assert len(batch_exps) == 10
    for exp_item in batch_exps:
        assert isinstance(exp_item, dict)
        assert pytest.approx(sum(exp_item.values()), abs=1e-3) == 1.0

    # 5. Zero-variance feature input handling
    zero_var_matrix = np.ones((25, 4))
    zero_clf = SklearnIF(random_state=42).fit(zero_var_matrix)
    zero_exp = ShapExplainer(zero_clf, feature_names=["z1", "z2", "z3", "z4"])
    exp_zero = zero_exp.explain_instance(zero_var_matrix[0])
    assert not any(np.isnan(v) or np.isinf(v) for v in exp_zero.values())
    assert sum(exp_zero.values()) == 1.0


def test_score_entities_dynamic_and_clean_identifiers():
    """
    Validates that score_entities evaluates transactions dynamically:
    - Produces varied risk scores (not uniform static 92.1).
    - Produces distinct reasons reflecting pattern matches.
    - Ensures entity identifiers are clean strings without brackets or quotes.
    """
    from backend.services.scoring import score_entities
    from ml.dataset_gen import generate_synthetic_dataset
    from backend.services.ingestion import process_raw_file

    raw_df = generate_synthetic_dataset(num_records=60, seed=42)
    processed_df = process_raw_file(raw_df)

    alerts = score_entities(processed_df)

    assert len(alerts) > 0

    # 1. Identifier cleanliness (no brackets, no quotes, no lists)
    for a in alerts:
        assert isinstance(a.entity_id, str)
        assert not a.entity_id.startswith("[")
        assert not a.entity_id.endswith("]")
        assert "'" not in a.entity_id
        assert '"' not in a.entity_id
        assert len(a.entity_id) > 0

    # 2. Dynamic varied risk scores (not all 92.1)
    risk_scores = [a.risk_score for a in alerts]
    unique_scores = set(risk_scores)
    assert len(unique_scores) > 1, f"Expected varied risk scores, got {unique_scores}"
    assert not all(s == 92.1 for s in risk_scores)

    # 3. Dynamic reasons
    reasons = [a.reason for a in alerts]
    unique_reasons = set(reasons)
    assert len(unique_reasons) > 1, f"Expected varied reasons, got {unique_reasons}"

    # 4. Valid entity types
    for a in alerts:
        assert a.entity_type in ("wallet", "ip")
        assert 0.0 <= a.risk_score <= 100.0
        assert 0.0 <= a.confidence <= 1.0
        assert isinstance(a.shap_explanation, dict)


