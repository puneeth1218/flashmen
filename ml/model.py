"""
IsolationForest Anomaly Detector & Risk Scoring Engine (Module M3).
Provides unsupervised training, 0-100 risk score calibration, explainability,
and human-readable anomaly attribution signal breakdowns for Bitcoin network monitoring.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from ml.feature_engineering import WALLET_FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# Standard forensic and investigative tag definitions
INVESTIGATIVE_TAG_MAPPING: Dict[str, str] = {
    "fan_out_ratio": "High Fan-Out (Peel Chain Pattern)",
    "unique_ips_used": "Rapid Multi-IP Broadcast",
    "total_volume_out": "Unusual Volume Surge (Outflow)",
    "total_volume_in": "Unusual Volume Surge (Inflow)",
    "fan_in_ratio": "High Fan-In (Mixer / Consolidation Pattern)",
    "tx_count": "Abnormal Transaction Velocity",
}


def get_investigative_tag(feature_name: str) -> str:
    """
    Maps a numeric feature name to a standardized human-readable investigative tag.

    Args:
        feature_name: Raw feature column name (e.g., 'unique_ips_used').

    Returns:
        str: Human-readable tag (e.g., 'Rapid Multi-IP Broadcast').
    """
    if feature_name in INVESTIGATIVE_TAG_MAPPING:
        return INVESTIGATIVE_TAG_MAPPING[feature_name]
    clean_name = feature_name.replace("_", " ").strip().title()
    return f"Unusual {clean_name} Surge"


class IsolationForestAnomalyDetector:
    """
    Unsupervised IsolationForest model tailored for Bitcoin network & transaction anomaly detection.

    Features:
    - Accepts scaled wallet feature DataFrames or NumPy arrays (from ml.feature_engineering).
    - Configured with unsupervised IsolationForest (default contamination=0.02, random_state=42).
    - Calibrates raw IsolationForest anomaly scores to an intuitive 0–100 Risk Score
      (where 100 represents the highest anomaly / threat level, and 0 represents normal behavior).
    - Provides feature attribution signal breakdowns and human-readable reason codes
      indicating which features pushed a flagged entity's anomaly score highest.
    - Directly attaches risk scores, anomaly flags, and top risk factors to wallet records.
    """

    def __init__(
        self,
        contamination: float = 0.02,
        random_state: int = 42,
        n_estimators: int = 100,
        max_samples: Union[str, float, int] = "auto"
    ):
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.max_samples = max_samples

        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=self.n_estimators,
            max_samples=self.max_samples
        )
        self.is_fitted: bool = False
        self.feature_names: List[str] = []
        self.score_min_: Optional[float] = None
        self.score_max_: Optional[float] = None
        self.baseline_mean_: Optional[np.ndarray] = None
        self.baseline_std_: Optional[np.ndarray] = None

    def _prepare_input(
        self,
        X: Union[pd.DataFrame, np.ndarray, pd.Series, List[Any]],
        is_fit: bool = False,
        feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Validates and standardizes input into a clean 2D NumPy array and feature names list.
        """
        if isinstance(X, pd.Series):
            df_temp = X.to_frame().T
            return self._prepare_input(df_temp, is_fit=is_fit, feature_names=feature_names)

        if isinstance(X, pd.DataFrame):
            if is_fit:
                numerical_df = X.select_dtypes(include=[np.number])
                if numerical_df.empty:
                    raise ValueError("DataFrame contains no numerical features for training.")
                names = list(numerical_df.columns)
                matrix = numerical_df.to_numpy(dtype=float)
            else:
                if self.feature_names and all(col in X.columns for col in self.feature_names):
                    numerical_df = X[self.feature_names]
                    names = self.feature_names
                else:
                    numerical_df = X.select_dtypes(include=[np.number])
                    names = list(numerical_df.columns) if not self.feature_names else self.feature_names
                matrix = numerical_df.to_numpy(dtype=float)
        else:
            # Array-like / NumPy ndarray
            arr = np.asarray(X, dtype=float)
            if arr.ndim == 1:
                matrix = arr.reshape(1, -1)
            elif arr.ndim == 2:
                matrix = arr
            else:
                raise ValueError(f"Expected 1D or 2D array, received ndim={arr.ndim}")

            if is_fit:
                if feature_names and len(feature_names) == matrix.shape[1]:
                    names = list(feature_names)
                elif matrix.shape[1] == len(WALLET_FEATURE_COLUMNS):
                    names = list(WALLET_FEATURE_COLUMNS)
                else:
                    names = [f"feature_{i+1}" for i in range(matrix.shape[1])]
            else:
                if self.feature_names and len(self.feature_names) == matrix.shape[1]:
                    names = self.feature_names
                elif matrix.shape[1] == len(WALLET_FEATURE_COLUMNS):
                    names = list(WALLET_FEATURE_COLUMNS)
                else:
                    names = [f"feature_{i+1}" for i in range(matrix.shape[1])]

        if matrix.size == 0 or matrix.shape[0] == 0:
            raise ValueError("Input data contains no samples.")

        # Sanitize any NaN or inf values
        matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
        return matrix, names

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        feature_names: Optional[List[str]] = None
    ) -> "IsolationForestAnomalyDetector":
        """
        Fits the unsupervised IsolationForest model on numerical feature vectors.

        Args:
            X: Scaled feature DataFrame or 2D NumPy array.
            feature_names: Optional feature column names (used when X is a NumPy array).

        Returns:
            self: Fitted detector instance.
        """
        matrix, names = self._prepare_input(X, is_fit=True, feature_names=feature_names)
        self.feature_names = names

        self.model.fit(matrix)

        # Record baseline distributions for attribution & score calibration
        self.baseline_mean_ = np.mean(matrix, axis=0)
        # Store safe baseline std (zero variance features remain 0.0 in baseline_std_)
        self.baseline_std_ = np.std(matrix, axis=0)

        train_scores = self.model.score_samples(matrix)
        self.score_min_ = float(np.min(train_scores))
        self.score_max_ = float(np.max(train_scores))
        self.is_fitted = True

        logger.info(
            f"Fitted IsolationForestAnomalyDetector on {matrix.shape[0]} samples, "
            f"{matrix.shape[1]} features. Score range: [{self.score_min_:.4f}, {self.score_max_:.4f}]"
        )
        return self

    def predict(self, X: Union[pd.DataFrame, np.ndarray, pd.Series]) -> np.ndarray:
        """
        Predicts anomaly labels (-1 for anomalies, +1 for inliers/normal).

        Args:
            X: Feature DataFrame or array.

        Returns:
            np.ndarray: Array of -1 and +1 labels.
        """
        if not self.is_fitted:
            raise ValueError("IsolationForestAnomalyDetector instance is not fitted yet. Call 'fit' before predict.")

        matrix, _ = self._prepare_input(X, is_fit=False)
        return self.model.predict(matrix)

    def score_samples(self, X: Union[pd.DataFrame, np.ndarray, pd.Series]) -> np.ndarray:
        """
        Calculates normalized risk scores between 0.0 (low risk / normal) and 100.0 (high risk / anomalous).

        IsolationForest score_samples() returns negative scores where lower values indicate
        greater anomaly severity. We calibrate these scores onto a 0–100 risk scale where
        100 represents the most severe outliers.

        Args:
            X: Feature DataFrame or array.

        Returns:
            np.ndarray: 1D array of calibrated risk scores strictly bounded in [0.0, 100.0].
        """
        if not self.is_fitted:
            raise ValueError("IsolationForestAnomalyDetector instance is not fitted yet. Call 'fit' before score_samples.")

        matrix, _ = self._prepare_input(X, is_fit=False)
        raw_scores = self.model.score_samples(matrix)

        min_val = min(float(np.min(raw_scores)), self.score_min_ if self.score_min_ is not None else -0.9)
        max_val = max(float(np.max(raw_scores)), self.score_max_ if self.score_max_ is not None else -0.35)

        if max_val <= min_val:
            scaled = np.zeros_like(raw_scores)
        else:
            scaled = 100.0 * (1.0 - (raw_scores - min_val) / (max_val - min_val))

        scaled = np.clip(scaled, 0.0, 100.0)
        return np.round(scaled, 2)

    def explain_instance(
        self,
        feature_row: Union[pd.Series, np.ndarray, Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Calculates feature attribution breakdown for a single instance, indicating which
        features pushed a flagged entity's risk score highest.

        Handles edge cases such as uniform data and zero-variance features without division-by-zero errors.

        Args:
            feature_row: Single entity feature row (Series, 1D array, 1-row DataFrame, or dict).

        Returns:
            Dict[str, float]: Dictionary mapping feature names to normalized impact weights summing to 1.0.
        """
        if not self.is_fitted:
            raise ValueError("IsolationForestAnomalyDetector must be fitted before generating explanations.")

        if isinstance(feature_row, dict):
            row_s = pd.Series(feature_row)
            matrix, names = self._prepare_input(row_s, is_fit=False)
        else:
            matrix, names = self._prepare_input(feature_row, is_fit=False)

        row_vals = matrix[0]

        # Calculate deviation relative to baseline population
        if self.baseline_mean_ is not None and self.baseline_std_ is not None:
            # Safe division: where std is zero or near zero, use absolute difference
            safe_std = np.where(self.baseline_std_ > 1e-9, self.baseline_std_, 1.0)
            deviations = np.abs(row_vals - self.baseline_mean_) / safe_std
        else:
            deviations = np.abs(row_vals)

        total_dev = float(np.sum(deviations))
        if total_dev <= 1e-9 or np.isnan(total_dev):
            equal_weight = round(1.0 / len(names), 4)
            return {name: equal_weight for name in names}

        weights = deviations / total_dev
        return {
            name: round(float(w), 4)
            for name, w in zip(names, weights)
        }

    def get_signal_breakdown(
        self,
        feature_row: Union[pd.Series, np.ndarray, Dict[str, Any], pd.DataFrame],
        top_n: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Convenience method returning the feature attribution breakdown sorted by impact descending.

        Args:
            feature_row: Feature representation for an instance.
            top_n: Optional integer limiting the number of returned top signals.

        Returns:
            Dict[str, float]: Ordered dictionary of feature impacts.
        """
        attributions = self.explain_instance(feature_row)
        sorted_items = sorted(attributions.items(), key=lambda x: x[1], reverse=True)
        if top_n is not None and top_n > 0:
            sorted_items = sorted_items[:top_n]
        return dict(sorted_items)

    def get_top_factors(
        self,
        feature_row: Union[pd.Series, np.ndarray, Dict[str, Any], pd.DataFrame],
        top_n: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Extracts the top contributing features with their human-readable investigative tags.

        Args:
            feature_row: Single entity feature row.
            top_n: Number of top factors to return (default 3).

        Returns:
            List[Tuple[str, str, float]]: List of (feature_name, investigative_tag, weight) tuples.
        """
        breakdown = self.get_signal_breakdown(feature_row, top_n=top_n)
        return [
            (feat, get_investigative_tag(feat), weight)
            for feat, weight in breakdown.items()
        ]

    def get_investigative_tags(
        self,
        feature_row: Union[pd.Series, np.ndarray, Dict[str, Any], pd.DataFrame],
        top_n: int = 3
    ) -> List[str]:
        """
        Extracts human-readable investigative tags for the top contributing factors.

        Args:
            feature_row: Single entity feature row.
            top_n: Number of top tags to return (default 3).

        Returns:
            List[str]: List of human-readable investigative tags.
        """
        factors = self.get_top_factors(feature_row, top_n=top_n)
        return [tag for _, tag, _ in factors]

    def get_anomaly_reason(
        self,
        feature_row: Union[pd.Series, np.ndarray, Dict[str, Any], pd.DataFrame],
        top_n: int = 2
    ) -> str:
        """
        Generates a human-readable forensic summary string explaining the anomaly classification.

        Args:
            feature_row: Single entity feature row.
            top_n: Number of factors to cite in the summary.

        Returns:
            str: Summary string, e.g. "Flagged due to Rapid Multi-IP Broadcast (78.2%), Unusual Volume Surge (21.8%)".
        """
        factors = self.get_top_factors(feature_row, top_n=top_n)
        if not factors:
            return "Normal network activity consistent with baseline."
        details = [f"{tag} ({weight * 100:.1f}%)" for _, tag, weight in factors if weight > 0]
        if not details:
            return "Normal network activity consistent with baseline."
        return "Flagged due to: " + ", ".join(details)

    def get_feature_attributions(
        self,
        X: Union[pd.DataFrame, np.ndarray]
    ) -> List[Dict[str, float]]:
        """
        Computes signal breakdowns for each sample in a batch X.

        Args:
            X: 2D feature DataFrame or array.

        Returns:
            List[Dict[str, float]]: List of feature attribution dictionaries.
        """
        if isinstance(X, pd.DataFrame):
            return [self.explain_instance(X.iloc[i]) for i in range(len(X))]
        matrix, _ = self._prepare_input(X, is_fit=False)
        return [self.explain_instance(matrix[i]) for i in range(len(matrix))]

    def score_and_explain(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        anomaly_threshold: float = 60.0,
        top_n: int = 3
    ) -> pd.DataFrame:
        """
        Evaluates feature records, computes calibrated 0–100 risk scores, and directly attaches
        interpretability fields (is_anomaly, top_risk_factors, top_features, signal_breakdown, reason)
        to the final scored records.

        Args:
            X: Ingested feature DataFrame (e.g. from extract_wallet_features) or 2D array.
            anomaly_threshold: Risk score cutoff (default 60.0) above which an entity is flagged.
            top_n: Number of top contributing factors to include (default 3).

        Returns:
            pd.DataFrame: Scored records with attached explainability and risk attribution metadata.
        """
        if not self.is_fitted:
            raise ValueError("IsolationForestAnomalyDetector must be fitted before calling score_and_explain.")

        if isinstance(X, pd.DataFrame):
            scored_df = X.copy()
        else:
            matrix, names = self._prepare_input(X, is_fit=False)
            scored_df = pd.DataFrame(matrix, columns=names)

        # 1. Compute calibrated risk scores and binary predictions
        risk_scores = self.score_samples(X)
        preds = self.predict(X)

        scored_df["risk_score"] = risk_scores
        scored_df["is_anomaly"] = (risk_scores >= anomaly_threshold) | (preds == -1)

        # 2. Extract feature-level attributions and human-readable tags
        top_factors_list: List[List[str]] = []
        top_features_list: List[List[str]] = []
        breakdowns_list: List[Dict[str, float]] = []
        reasons_list: List[str] = []

        for i in range(len(scored_df)):
            row = scored_df.iloc[i]
            breakdown = self.get_signal_breakdown(row, top_n=top_n)
            top_features = list(breakdown.keys())
            top_tags = [get_investigative_tag(f) for f in top_features]

            if bool(scored_df["is_anomaly"].iloc[i]):
                reason = self.get_anomaly_reason(row, top_n=min(2, top_n))
                top_risk_factors = top_tags
            else:
                reason = "Normal baseline behavior."
                top_risk_factors = []

            top_factors_list.append(top_risk_factors)
            top_features_list.append(top_features)
            breakdowns_list.append(breakdown)
            reasons_list.append(reason)

        scored_df["top_risk_factors"] = top_factors_list
        scored_df["top_features"] = top_features_list
        scored_df["signal_breakdown"] = breakdowns_list
        scored_df["reason"] = reasons_list

        return scored_df
