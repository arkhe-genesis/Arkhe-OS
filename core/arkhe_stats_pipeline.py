# core/arkhe_stats_pipeline.py
"""
Unified statistical analysis: sklearn + xgboost + octonionic metrics.
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import xgboost as xgb

class OctonionicAnalyzer:
    """Analyze octonionic correlations with classical + gradient boosting ML."""

    def __init__(self, data_path: str):
        self.df = pd.read_csv(data_path)
        self.scaler = StandardScaler()

    def prepare_features(self, feature_cols: list, target_col: str):
        """Prepare features with scaling and octonionic engineering."""
        X = self.df[feature_cols].copy()
        y = self.df[target_col]

        # Octonionic feature engineering
        X['Z_over_A'] = X['Z'] / (X['A'] + 1e-10)
        X['Asymmetry'] = np.abs(X['A'] - 2*X['Z']) / X['A']
        X['logT12'] = np.log10(self.df['HalfLife_seconds'].clip(1e-20) + 1)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y, X.columns.tolist()

    def compare_models(self, X, y, cv=5):
        """Compare linear (sklearn) vs gradient boosting (xgboost) performance."""
        from sklearn.linear_model import LinearRegression, Ridge
        from sklearn.ensemble import RandomForestRegressor

        models = {
            'Linear': LinearRegression(),
            'Ridge': Ridge(alpha=1.0),
            'XGBoost': xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
        }

        results = {}
        for name, model in models.items():
            scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
            results[name] = {
                'r2_mean': scores.mean(),
                'r2_std': scores.std(),
                'model': model
            }
            print(f"{name:12s}: R² = {scores.mean():.4f} ± {scores.std():.4f}")

        return results

    def explain_octonionic_importance(self, model, feature_names: list):
        """Extract and visualize feature importance for octonionic interpretation."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            return None

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        return importance_df
