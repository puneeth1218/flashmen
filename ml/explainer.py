"""
SHAP TreeExplainer Wrapper (Module M3).
Computes local Shapley attribution values from fitted IsolationForest models
to provide explainability, forensic reason codes, and investigative tags for flagged anomaly alerts.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np

# Backward compatibility for NumPy 2.0+ with shap internals
if not hasattr(np, "bool"):
    np.bool = bool
if not hasattr(np, "float"):
    np.float = float
if not hasattr(np, "int"):
    np.int = int

import pandas as pd
import shap
from sklearn.ensemble import IsolationForest

from ml.model import get_investigative_tag, INVESTIGATIVE_TAG_MAPPING

logger = logging.getLogger(__name__)


class ShapExplainer:
    """
    Wrapper around SHAP (SHapley Additive exPlanations) TreeExplainer
    specifically tailored for Isolation Forest anomaly detection.

    Features:
    - True Shapley feature attribution values computed from fitted tree ensembles.
    - Robust dimension and output formatting handling across SHAP/sklearn versions.
    - Normalized absolute impact percentages summing strictly to 1.0 (100%).
    - Mapping of top anomaly drivers to standardized investigative forensic tags.
    - Graceful fallback for unfitted models, single instances, and zero-variance features.
    """

    def __init__(
        self,
        model_wrapper: Any = None,
        feature_names: Optional[List[str]] = None,
        background_data: Optional[Union[np.ndarray, pd.DataFrame]] = None
    ):
        """
        Initializes the ShapExplainer.

        Args:
            model_wrapper: Fitted IsolationForestAnomalyDetector, IsolationForest, or None.
            feature_names: Optional explicit list of feature names.
            background_data: Optional background dataset for TreeExplainer interventional perturbation.
        """
        self.model_wrapper = model_wrapper
        self.feature_names: List[str] = list(feature_names) if feature_names else []
        self.raw_model: Optional[IsolationForest] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.background_data = background_data

        if model_wrapper is not None:
            self._init_explainer(model_wrapper, feature_names=feature_names, background_data=background_data)

    def _init_explainer(
        self,
        model_wrapper: Any,
        feature_names: Optional[List[str]] = None,
        background_data: Optional[Union[np.ndarray, pd.DataFrame]] = None
    ) -> bool:
        """
        Extracts the underlying IsolationForest model and constructs shap.TreeExplainer.
        """
        # 1. Extract underlying IsolationForest
        if hasattr(model_wrapper, "model") and isinstance(model_wrapper.model, IsolationForest):
            self.raw_model = model_wrapper.model
            if not self.feature_names and hasattr(model_wrapper, "feature_names") and model_wrapper.feature_names:
                self.feature_names = list(model_wrapper.feature_names)
        elif isinstance(model_wrapper, IsolationForest):
            self.raw_model = model_wrapper
        else:
            self.raw_model = getattr(model_wrapper, "model", model_wrapper)

        if feature_names:
            self.feature_names = list(feature_names)

        bg = background_data if background_data is not None else self.background_data

        if self.raw_model is not None and hasattr(self.raw_model, "estimators_"):
            try:
                if bg is not None:
                    if isinstance(bg, pd.DataFrame):
                        bg_numeric = bg.select_dtypes(include=[np.number]).to_numpy(dtype=float)
                    else:
                        bg_numeric = np.asarray(bg, dtype=float)
                    self.explainer = shap.TreeExplainer(self.raw_model, data=bg_numeric)
                else:
                    self.explainer = shap.TreeExplainer(self.raw_model)
                return True
            except Exception as e:
                logger.warning(f"Failed to initialize shap.TreeExplainer: {e}. Falling back to baseline attribution.")
                self.explainer = None
                return False
        return False

    def _prepare_input(
        self,
        feature_input: Union[pd.Series, pd.DataFrame, Dict[str, Any], np.ndarray, List[Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Standardizes input feature vectors into a 2D float NumPy array and list of feature names.
        """
        # 1. pd.Series
        if isinstance(feature_input, pd.Series):
            if self.feature_names and all(col in feature_input.index for col in self.feature_names):
                sub = feature_input[self.feature_names]
                X = sub.to_numpy(dtype=float).reshape(1, -1)
                return X, list(self.feature_names)
            numeric_s = feature_input[[k for k in feature_input.index if k not in ("entity_id", "wallet_id", "address")]]
            try:
                numeric_s = numeric_s.astype(float)
                return numeric_s.to_numpy(dtype=float).reshape(1, -1), list(numeric_s.index)
            except Exception:
                num_only = pd.to_numeric(numeric_s, errors="coerce").dropna()
                return num_only.to_numpy(dtype=float).reshape(1, -1), list(num_only.index)

        # 2. dict
        if isinstance(feature_input, dict):
            s = pd.Series(feature_input)
            return self._prepare_input(s)

        # 3. pd.DataFrame
        if isinstance(feature_input, pd.DataFrame):
            if self.feature_names and all(col in feature_input.columns for col in self.feature_names):
                sub_df = feature_input[self.feature_names].astype(float)
                return sub_df.to_numpy(dtype=float), list(self.feature_names)
            num_df = feature_input.select_dtypes(include=[np.number]).astype(float)
            cols = [c for c in num_df.columns if c not in ("entity_id", "wallet_id", "address")]
            return num_df[cols].to_numpy(dtype=float), cols

        # 4. np.ndarray or list
        arr = np.asarray(feature_input, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        names = self.feature_names if (self.feature_names and len(self.feature_names) == arr.shape[1]) else [
            f"feature_{i}" for i in range(arr.shape[1])
        ]
        return arr, names

    def _compute_shap_matrix(self, X: np.ndarray) -> np.ndarray:
        """
        Computes raw SHAP values matrix of shape (N, D).
        Accounts for multi-output lists and dimensional variances across SHAP/sklearn versions.
        """
        if self.explainer is None:
            if self.model_wrapper is not None:
                self._init_explainer(self.model_wrapper)
            if self.explainer is None:
                raise RuntimeError("TreeExplainer is not initialized or model is not fitted.")

        try:
            raw_shap = self.explainer.shap_values(X, check_additivity=False)
        except TypeError:
            raw_shap = self.explainer.shap_values(X)

        # Account for multi-output (list of arrays)
        if isinstance(raw_shap, list):
            raw_shap = raw_shap[0]

        # Account for Explanation object (shap >= 0.40)
        if hasattr(raw_shap, "values"):
            raw_shap = raw_shap.values

        raw_matrix = np.asarray(raw_shap, dtype=float)

        # Dimension flattening/handling
        if raw_matrix.ndim == 3:
            if raw_matrix.shape[2] == 1:
                raw_matrix = raw_matrix[:, :, 0]
            elif raw_matrix.shape[0] == 1:
                raw_matrix = raw_matrix[0, :, :]
            else:
                raw_matrix = raw_matrix[:, :, 0]
        elif raw_matrix.ndim == 1:
            raw_matrix = raw_matrix.reshape(1, -1)

        return raw_matrix

    def _normalize_row_attribution(self, row_shap: np.ndarray, names: List[str]) -> Dict[str, float]:
        """
        Extracts absolute impacts, normalizes them so they sum strictly to 1.0 (100%),
        and maps them to feature names.
        """
        abs_vals = np.abs(row_shap)
        abs_vals = np.nan_to_num(abs_vals, nan=0.0, posinf=0.0, neginf=0.0)
        total_abs = float(np.sum(abs_vals))

        if total_abs <= 1e-9 or len(names) == 0:
            # Zero-variance or baseline-identical instance -> equal attribution
            eq = round(1.0 / max(len(names), 1), 4)
            res = {name: eq for name in names}
            diff = round(1.0 - sum(res.values()), 4)
            if diff != 0 and names:
                res[names[0]] = round(res[names[0]] + diff, 4)
            return res

        weights = abs_vals / total_abs
        attribution = {
            name: round(float(w), 4)
            for name, w in zip(names, weights)
        }

        # Correct the rounding residual so the returned values sum exactly to 1.0.
        if names:
            top_key = max(attribution, key=attribution.get)
            residual = 1.0 - sum(attribution.values())
            attribution[top_key] += residual

        return attribution

    def explain_instance(
        self,
        feature_row: Union[pd.Series, pd.DataFrame, Dict[str, Any], np.ndarray, List[Any]]
    ) -> Dict[str, float]:
        """
        Calculates local SHAP feature attribution breakdown for a single entity.

        Args:
            feature_row: Single entity feature representation.

        Returns:
            Dict[str, float]: Dictionary mapping feature names to normalized impact weights summing to 1.0.
        """
        X, names = self._prepare_input(feature_row)

        # Attempt true SHAP TreeExplainer calculation
        try:
            shap_matrix = self._compute_shap_matrix(X)
            return self._normalize_row_attribution(shap_matrix[0], names)
        except Exception as e:
            logger.debug(f"SHAP TreeExplainer execution failed or uninitialized ({e}); using graceful fallback.")

            # Graceful Fallback 1: Use model_wrapper's explain_instance if available (e.g. IsolationForestAnomalyDetector Z-score baseline)
            if self.model_wrapper is not None and hasattr(self.model_wrapper, "explain_instance"):
                try:
                    return self.model_wrapper.explain_instance(feature_row)
                except Exception:
                    pass

            # Graceful Fallback 2: Safe uniform distribution summing strictly to 1.0
            if not names:
                names = ["fan_out_ratio", "unique_ips_used", "total_volume_out", "total_volume_in"]

            eq = round(1.0 / len(names), 4)
            res = {name: eq for name in names}
            diff = round(1.0 - sum(res.values()), 4)
            if diff != 0 and names:
                res[names[0]] = round(res[names[0]] + diff, 4)
            return res

    def explain_dataset(
        self,
        X: Union[pd.DataFrame, np.ndarray]
    ) -> List[Dict[str, float]]:
        """
        Calculates SHAP attributions across a dataset in batch mode.

        Args:
            X: 2D feature DataFrame or NumPy array.

        Returns:
            List[Dict[str, float]]: List of feature attribution dictionaries per sample.
        """
        matrix, names = self._prepare_input(X)
        try:
            shap_matrix = self._compute_shap_matrix(matrix)
            return [self._normalize_row_attribution(row, names) for row in shap_matrix]
        except Exception:
            return [self.explain_instance(row) for row in matrix]

    def get_top_factors(
        self,
        feature_row: Union[pd.Series, pd.DataFrame, Dict[str, Any], np.ndarray, List[Any]],
        top_n: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Extracts top contributing features mapped to standardized investigative tags.

        Args:
            feature_row: Entity feature vector.
            top_n: Number of top factors to return (default 3).

        Returns:
            List[Tuple[str, str, float]]: List of (feature_name, investigative_tag, weight) tuples.
        """
        breakdown = self.explain_instance(feature_row)
        sorted_items = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        if top_n > 0:
            sorted_items = sorted_items[:top_n]
        return [
            (feat, get_investigative_tag(feat), weight)
            for feat, weight in sorted_items
        ]

    def get_investigative_tags(
        self,
        feature_row: Union[pd.Series, pd.DataFrame, Dict[str, Any], np.ndarray, List[Any]],
        top_n: int = 3
    ) -> List[str]:
        """
        Extracts human-readable investigative tags for the top contributing factors.
        """
        factors = self.get_top_factors(feature_row, top_n=top_n)
        return [tag for _, tag, _ in factors]

    def get_anomaly_reason(
        self,
        feature_row: Union[pd.Series, pd.DataFrame, Dict[str, Any], np.ndarray, List[Any]],
        top_n: int = 2
    ) -> str:
        """
        Generates a human-readable forensic summary string explaining the anomaly classification.
        """
        factors = self.get_top_factors(feature_row, top_n=top_n)
        if not factors:
            return "Normal network activity consistent with baseline."
        details = [f"{tag} ({weight * 100:.1f}%)" for _, tag, weight in factors if weight > 0]
        if not details:
            return "Normal network activity consistent with baseline."
        return f"Flagged due to {', '.join(details)}."

    def get_shap_matrix(
        self,
        X: Union[pd.DataFrame, np.ndarray]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Returns raw SHAP attribution matrix (N, D) and feature names.
        """
        matrix, names = self._prepare_input(X)
        shap_matrix = self._compute_shap_matrix(matrix)
        return shap_matrix, names
