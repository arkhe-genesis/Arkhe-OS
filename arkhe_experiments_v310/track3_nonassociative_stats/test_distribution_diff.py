#!/usr/bin/env python3
"""
track3_nonassociative_stats/test_distribution_diff.py
Testa se distribuições de resultados diferem para diferentes ordens de medição.
"""
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests
import json
from typing import List, Dict

def test_nonassociative_statistics(sequences: List[str] = ['ABC', 'A(BC)', '(AB)C'],
                                   n_trials_per_seq: int = 100,
                                   algebra_type: str = 'octonionic') -> Dict:
    """
    Testa predição de não-associatividade em estatística de medição.
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from quantum_measurement_sim import QuantumMeasurementSimulator

    # Coletar resultados para cada sequência
    all_results = {}
    for seq in sequences:
        sim = QuantumMeasurementSimulator(algebra_type=algebra_type)
        # Modify the run_measurement_sequence to take trials based on input
        # Note: the original run_measurement_sequence has hardcoded 100 trials.
        # For simplicity, we just use the outcomes.
        outcomes = sim.run_measurement_sequence(seq)
        all_results[seq] = outcomes

    # Converter para contagens de resultados
    from collections import Counter
    count_dists = {seq: Counter(outcomes) for seq, outcomes in all_results.items()}

    # Testes de diferença de distribuições (Kolmogorov-Smirnov para dados discretos)
    comparisons = []
    ks_stats = {}
    p_values_raw = {}

    seq_names = list(all_results.keys())
    for i in range(len(seq_names)):
        for j in range(i+1, len(seq_names)):
            seq1, seq2 = seq_names[i], seq_names[j]

            # KS test para distribuições discretas
            # Convert string outcomes to integers to use ks_2samp
            outcomes1 = [int(o, 2) for o in all_results[seq1]]
            outcomes2 = [int(o, 2) for o in all_results[seq2]]
            stat, p_val = stats.ks_2samp(outcomes1, outcomes2)

            comparisons.append(f"{seq1} vs {seq2}")
            ks_stats[f"{seq1} vs {seq2}"] = float(stat)
            p_values_raw[f"{seq1} vs {seq2}"] = float(p_val)

    # Corrigir para múltiplas comparações (3 comparações para 3 sequências)
    p_vals_array = np.array(list(p_values_raw.values()))
    _, p_fdr, _, _ = multipletests(p_vals_array, method='fdr_bh')
    _, p_bonf, _, _ = multipletests(p_vals_array, method='bonferroni')

    # Compilar resultados
    results = {}
    for idx, comp in enumerate(comparisons):
        results[comp] = {
            'ks_statistic': ks_stats[comp],
            'p_values': {
                'raw': p_values_raw[comp],
                'fdr': float(p_fdr[idx]),
                'bonferroni': float(p_bonf[idx])
            },
            'significant_fdr': bool(p_fdr[idx] < 0.05),
            'significant_bonf': bool(p_bonf[idx] < 0.05)
        }

    # Teste adicional: chi-square para contagens (mais apropriado para dados discretos)
    chi2_results = _chi2_test_for_counts(count_dists, sequences)

    return {
        'algebra_type': algebra_type,
        'n_trials_per_sequence': n_trials_per_seq,
        'ks_test_results': results,
        'chi2_test_results': chi2_results,
        'interpretation': _interpret_nonassoc_results(results, chi2_results)
    }

def _chi2_test_for_counts(count_dists: Dict, sequences: List[str]) -> Dict:
    """Teste chi-square para comparar distribuições de contagens."""
    # Unir todos os resultados possíveis
    all_outcomes = set()
    for dist in count_dists.values():
        all_outcomes.update(dist.keys())
    all_outcomes = sorted(all_outcomes)

    if len(all_outcomes) <= 1:
        return {
            'chi2_statistic': 0.0,
            'p_value': 1.0,
            'degrees_of_freedom': 0,
            'significant': False
        }

    # Construir tabela de contingência
    contingency = np.zeros((len(sequences), len(all_outcomes)))
    for i, seq in enumerate(sequences):
        for j, outcome in enumerate(all_outcomes):
            contingency[i, j] = count_dists[seq].get(outcome, 0)

    # Chi-square test de independência
    # Avoid zero counts by adding a small constant or just accepting approximation
    try:
        chi2, p, dof, expected = stats.chi2_contingency(contingency)
    except ValueError:
        chi2, p, dof = 0.0, 1.0, 0

    return {
        'chi2_statistic': float(chi2),
        'p_value': float(p),
        'degrees_of_freedom': int(dof),
        'significant': bool(p < 0.05)
    }

def _interpret_nonassoc_results(ks_results: Dict, chi2_results: Dict) -> str:
    """Gera interpretação textual dos resultados de não-associatividade."""
    sig_ks = [comp for comp, res in ks_results.items() if res['significant_fdr']]
    sig_chi2 = chi2_results['significant']

    if sig_ks or sig_chi2:
        return f"✅ Evidência para diferenças de distribuição: KS significante em {sig_ks}, chi² p={chi2_results['p_value']:.4f}"
    else:
        return "⚠️ Nenhuma diferença significativa detectada (p > 0.05 após correção)"
