"""
Unit tests for IsolationForest model wrapper and SHAP explainer.
"""

import pandas as pd
import numpy as np
from ml.model import IsolationForestAnomalyDetector
from ml.explainer import ShapExplainer


def test_isolation_forest_fit_predict():
    """
    Tests fitting and score calculations on IsolationForest wrapper.
    """
    detector = IsolationForestAnomalyDetector(contamination=0.1)
    
    # Create sample numerical dataframe
    X = pd.DataFrame({
        "feature1": np.random.normal(0, 1, 50),
        "feature2": np.random.normal(5, 2, 50)
    })
    
    detector.fit(X)
    assert detector.is_fitted
    
    predictions = detector.predict(X)
    assert len(predictions) == 50
    
    scores = detector.score_samples(X)
    assert len(scores) == 50
    assert (scores >= 0.0).all() and (scores <= 100.0).all()


def test_shap_explainer():
    """
    Tests SHAP explainer attribution output structure.
    """
    explainer = ShapExplainer()
    sample_series = pd.Series({"feature1": 1.5, "feature2": 4.2})
    explanation = explainer.explain_instance(sample_series)
    
    assert isinstance(explanation, dict)
    assert "feature1" in explanation
    assert "feature2" in explanation
