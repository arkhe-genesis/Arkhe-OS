# core/spsa_tabula_prior.py
"""
Use Tabula Oracle predictions as prior for AdaptiveSPSA initialization.
Accelerates convergence by starting near predicted optimal regime.
"""
import numpy as np
import xgboost as xgb
from pathlib import Path
from typing import Optional, Dict

class TabulaSPSAPrior:
    """Provide SPSA initialization priors based on Tabula Oracle predictions."""

    def __init__(self, model_path: str = 'models/tabula_ame2020/tabula_oracle.json',
                 metadata_path: str = 'models/tabula_ame2020/metadata.json'):
        """Load trained Tabula Oracle model."""
        import json
        self.model = xgb.XGBRegressor()
        self.model.load_model(model_path)

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        self.feature_names = metadata['feature_names']
        self.capture_threshold = metadata.get('capture_threshold', 0.3)

    def predict_regime(self, nuclear_features: Dict[str, float]) -> Dict[str, any]:
        """
        Predict coherence regime from nuclear/system features.

        Args:
            nuclear_features: dict with keys matching model feature_names

        Returns:
            dict with iao_pred, capture_likely, suggested_params
        """
        import pandas as pd

        # Prepare feature vector
        X = pd.DataFrame([nuclear_features])[self.feature_names]

        # Predict IAO
        iao_pred = self.model.predict(X)[0]
        capture_likely = iao_pred < self.capture_threshold

        # Suggest SPSA initialization based on predicted regime
        if capture_likely:
            # CAPTURE regime: start with higher coupling, lower threshold
            suggested_params = {
                'kappa': np.random.uniform(0.9, 1.3),  # Higher coupling
                'lambda_l1': np.random.uniform(0.001, 0.005),  # Less regularization
                'threshold': np.random.uniform(0.05, 0.12),  # Lower threshold
                'embedding_dim': 3  # Keep dimensionality stable
            }
        else:
            # Non-CAPTURE: start more exploratory
            suggested_params = {
                'kappa': np.random.uniform(0.5, 0.9),  # Lower coupling
                'lambda_l1': np.random.uniform(0.005, 0.01),  # More regularization
                'threshold': np.random.uniform(0.12, 0.25),  # Higher threshold
                'embedding_dim': np.random.choice([2, 3, 4])  # Explore dimensions
            }

        return {
            'iao_pred': float(iao_pred),
            'capture_likely': bool(capture_likely),
            'suggested_params': suggested_params,
            'confidence': float(min(1.0, 0.5 + abs(iao_pred - 0.5)))  # Heuristic confidence
        }

    def initialize_spsa_with_prior(self, nuclear_features: Dict[str, float],
                                   param_bounds: list) -> np.ndarray:
        """
        Initialize SPSA parameters using Tabula prior, respecting bounds.

        Args:
            nuclear_features: features for regime prediction
            param_bounds: list of (min, max) for [kappa, lambda_l1, threshold, embedding_dim]

        Returns:
            theta: initial parameter array for SPSA
        """
        prediction = self.predict_regime(nuclear_features)
        suggested = prediction['suggested_params']

        # Map suggested params to theta array with bounds clipping
        theta = np.array([
            np.clip(suggested['kappa'], *param_bounds[0]),
            np.clip(suggested['lambda_l1'], *param_bounds[1]),
            np.clip(suggested['threshold'], *param_bounds[2]),
            np.clip(suggested['embedding_dim'], *param_bounds[3])
        ], dtype=float)

        return theta
