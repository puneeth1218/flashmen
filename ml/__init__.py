"""
Machine Learning Module.
Provides feature engineering, anomaly detection models, SHAP explainers, and synthetic data generation.
"""
from .feature_engineering import extract_features
from .model import IsolationForestAnomalyDetector
from .explainer import ShapExplainer
from .dataset_gen import generate_synthetic_dataset

__all__ = [
    "extract_features",
    "IsolationForestAnomalyDetector",
    "ShapExplainer",
    "generate_synthetic_dataset"
]
