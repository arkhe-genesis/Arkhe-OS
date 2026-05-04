# core/tabula_sklearn_integration.py
"""
Bridge Tabula Oracle (XGBoost) with sklearn pipelines for unified analysis.
"""
from core.arkhe_stats_pipeline import OctonionicAnalyzer
from core.arkhe_tabula import TabulaOracle

def unified_octonionic_workflow(data_csv: str, target_col: str = 'OctonionicAnomalyIndex'):
    """End-to-end workflow: EDA → model comparison → Tabula deployment."""

    # 1. Load and prepare data
    analyzer = OctonionicAnalyzer(data_csv)
    feature_cols = ['Z', 'A', 'BindingEnergy_MeV_per_nucleon', 'HalfLife_seconds']
    X, y, feature_names = analyzer.prepare_features(feature_cols, target_col)

    # 2. Compare models
    print("\n📊 Model Comparison:")
    results = analyzer.compare_models(X, y)

    # 3. Train best model (XGBoost) and export as Tabula Oracle
    best_model = results['XGBoost']['model']
    best_model.fit(X, y)

    # 4. Export to Tabula format
    oracle = TabulaOracle()
    oracle.model = best_model
    oracle.feature_names = feature_names
    oracle.save_model('models/tabula_oracle_unified.json')

    # 5. Explain octonionic correlations
    importance = analyzer.explain_octonionic_importance(best_model, feature_names)
    print(f"\n🔍 Top Octonionic Correlates:")
    print(importance.head(10).to_string(index=False))

    return {
        'models': results,
        'oracle_path': 'models/tabula_oracle_unified.json',
        'feature_importance': importance
    }
