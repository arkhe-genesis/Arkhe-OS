#!/usr/bin/env python3
"""
track2_fluid_intention_modulation.py
Testa se sinal EEG de observador humano modula a força do vórtice fingerprint 0.58.
"""
import numpy as np

def compute_cohens_d(x, y):
    x = np.array(x)
    y = np.array(y)
    nx = len(x)
    ny = len(y)
    if nx == 0 or ny == 0: return 0.0
    dof = nx + ny - 2
    pool_std = np.sqrt(((nx-1)*np.var(x, ddof=1) + (ny-1)*np.var(y, ddof=1)) / dof)
    if pool_std == 0: return 0.0
    return (np.mean(x) - np.mean(y)) / pool_std

def test_intention_vortex_coupling(eeg_features_list, vortex_strength_measurements):
    """
    Hipótese: feature de intenção (ex: potência gamma) correlaciona com
    amplitude do vórtice injetado no campo fluido.
    """
    from scipy import stats
    from statsmodels.stats.multitest import multipletests

    # Extrair feature composta de intenção
    intention_scores = [f['intention_score'] for f in eeg_features_list]

    # Calcular correlação com força do vórtice medida
    r_pearson, p_raw = stats.pearsonr(intention_scores, vortex_strength_measurements)

    # Corrigir para múltiplas comparações (se testar múltiplas features)
    p_corrected = multipletests([p_raw], method='fdr_bh')[1][0]

    # Efeito tamanho (Cohen's d)
    cohens_d = compute_cohens_d(intention_scores, vortex_strength_measurements)

    return {
        'pearson_r': float(r_pearson),
        'p_value_raw': float(p_raw),
        'p_value_fdr_corrected': float(p_corrected),
        'cohens_d': float(cohens_d),
        'significant': p_corrected < 0.05 and abs(r_pearson) > 0.3
    }
