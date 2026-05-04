#!/usr/bin/env python3
"""
track2_intention_correlation/correlate_intention_sync.py
Correlaciona features de intenção EEG com tempo de sincronização do Merkabah.
"""
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
import json
from typing import List, Dict

def test_intention_modulation(eeg_features_list: List[Dict],
                             sync_times: List[float],
                             time_alignment_s: float = 1.0,
                             correction_method: str = 'fdr_bh') -> Dict:
    """
    Testa correlação entre intenção (EEG) e sincronização (Merkabah).
    """
    if len(eeg_features_list) != len(sync_times):
        return {'error': 'Mismatched data lengths'}

    # Extrair matriz de features
    feature_names = list(eeg_features_list[0].keys())
    X = np.array([[f[name] for name in feature_names]
                  for f in eeg_features_list])
    y = np.array(sync_times)

    # Remover NaNs
    valid_mask = ~(np.any(np.isnan(X), axis=1) | np.isnan(y))
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]

    if len(X_clean) < 20:
        return {'error': 'Insufficient valid data points'}

    # Calcular correlações (Pearson e Spearman para robustez)
    correlations = {}
    p_values_raw = {}

    for i, name in enumerate(feature_names):
        # Pearson
        r_pearson, p_pearson = stats.pearsonr(X_clean[:, i], y_clean)
        # Spearman (não-paramétrico)
        r_spearman, p_spearman = stats.spearmanr(X_clean[:, i], y_clean)

        correlations[name] = {
            'pearson_r': float(r_pearson),
            'spearman_rho': float(r_spearman)
        }
        p_values_raw[name] = {
            'pearson_p': float(p_pearson),
            'spearman_p': float(p_spearman)
        }

    # Corrigir para múltiplas comparações
    p_vals_pearson = np.array([p_values_raw[name]['pearson_p'] for name in feature_names])
    p_vals_spearman = np.array([p_values_raw[name]['spearman_p'] for name in feature_names])

    # FDR (Benjamini-Hochberg) e Bonferroni
    _, p_fdr_pearson, _, _ = multipletests(p_vals_pearson, method='fdr_bh')
    _, p_bonf_pearson, _, _ = multipletests(p_vals_pearson, method='bonferroni')
    _, p_fdr_spearman, _, _ = multipletests(p_vals_spearman, method='fdr_bh')
    _, p_bonf_spearman, _, _ = multipletests(p_vals_spearman, method='bonferroni')

    # Compilar resultados
    results = {}
    for i, name in enumerate(feature_names):
        results[name] = {
            'correlations': correlations[name],
            'p_values': {
                'raw_pearson': float(p_values_raw[name]['pearson_p']),
                'raw_spearman': float(p_values_raw[name]['spearman_p']),
                'fdr_pearson': float(p_fdr_pearson[i]),
                'bonferroni_pearson': float(p_bonf_pearson[i]),
                'fdr_spearman': float(p_fdr_spearman[i]),
                'bonferroni_spearman': float(p_bonf_spearman[i])
            },
            'significant_fdr_pearson': bool(p_fdr_pearson[i] < 0.05),
            'significant_bonf_pearson': bool(p_bonf_pearson[i] < 0.05)
        }

    # Feature composta de intenção (se existir)
    if 'intention_score' in feature_names:
        r_comp, p_comp = stats.pearsonr(
            X_clean[:, feature_names.index('intention_score')], y_clean
        )
        results['intention_score']['composite_correlation'] = {
            'pearson_r': float(r_comp),
            'p_value_raw': float(p_comp),
            'p_value_fdr': float(multipletests([p_comp], method='fdr_bh')[1][0])
        }

    return {
        'n_valid_trials': len(X_clean),
        'feature_results': results,
        'correction_method': correction_method,
        'interpretation': _interpret_correlation_results(results)
    }

def _interpret_correlation_results(results: Dict) -> str:
    """Gera interpretação textual dos resultados de correlação."""
    significant = [name for name, res in results.items()
                   if res.get('significant_fdr_pearson', False)]

    if not significant:
        return "Nenhuma correlação significativa após correção FDR (p < 0.05)"
    elif 'intention_score' in significant:
        return f"✅ Correlação significativa entre intenção composta e sincronização: {results['intention_score']['correlations']['pearson_r']:.3f}"
    else:
        return f"⚠️ Correlações significativas em features individuais: {significant}"
