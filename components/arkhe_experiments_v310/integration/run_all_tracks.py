#!/usr/bin/env python3
"""
integration/run_all_tracks.py
Executa os três tracks experimentais e integra resultados.
"""
import numpy as np
import json
from typing import Dict, List
from datetime import datetime
import sys
import os

# Add parent directory to path so we can import tracks
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_integrated_experiment(config_path: str = 'config/statistical_plan.json'):
    """Executa todos os tracks e gera relatório integrado."""

    # Carregar configuração
    # Handle relative pathing from script run location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_config_path = os.path.join(base_dir, config_path)

    with open(full_config_path, 'r') as f:
        config = json.load(f)

    print("🔬 ARKHE OS v∞.310 — INTEGRATED EXPERIMENTAL FRAMEWORK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Config: {full_config_path}")

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'version': 'v∞.310'
        },
        'tracks': {}
    }

    # Track 1: Mass-dependence
    print("\n📊 Track 1: Mass-dependence test (τ ∝ 1/√N)...")
    from track1_mass_dependence.analyze_mass_scaling import test_mass_dependence
    track1_result = test_mass_dependence(
        n_values=config['track1']['n_values'],
        n_trials=config['track1']['n_trials']
    )
    results['tracks']['mass_dependence'] = track1_result
    print(f"   Result: {track1_result.get('bayesian_evidence', {}).get('interpretation', 'N/A')} evidence for mass-dependence")

    # Track 2: Intention correlation
    print("\n🧠 Track 2: Intention↔synchronization correlation...")
    from track2_intention_correlation.correlate_intention_sync import test_intention_modulation

    # Dados simulados para demonstração
    np.random.seed(42)
    n_trials = config['track2']['n_trials']
    eeg_features = [{'intention_score': float(np.random.normal(0.5, 0.2))} for _ in range(n_trials)]
    sync_times = [float(np.random.exponential(2.0) + 0.3 * f['intention_score']) for f in eeg_features]

    track2_result = test_intention_modulation(eeg_features, sync_times)
    results['tracks']['intention_correlation'] = track2_result
    print(f"   Result: {track2_result.get('interpretation', 'N/A')}")

    # Track 3: Non-associative statistics
    print("\n🔢 Track 3: Non-associative statistics test...")
    from track3_nonassociative_stats.test_distribution_diff import test_nonassociative_statistics
    track3_result = test_nonassociative_statistics(
        sequences=config['track3']['sequences'],
        n_trials_per_seq=config['track3']['n_trials'],
        algebra_type=config['track3']['algebra_type']
    )
    results['tracks']['nonassociative_stats'] = track3_result
    print(f"   Result: {track3_result.get('interpretation', 'N/A')}")

    # Validação cruzada entre tracks
    print("\n🔗 Cross-validation between tracks...")
    cross_validation = _cross_validate_tracks(results['tracks'])
    results['cross_validation'] = cross_validation
    print(f"   Consistency: {cross_validation['overall_consistency']}")

    # Bayes factor combinado (meta-análise)
    print("\n📈 Combined Bayesian evidence...")
    combined_evidence = _compute_combined_bayes_factor(results['tracks'])
    results['combined_evidence'] = combined_evidence
    print(f"   Combined Bayes factor: {combined_evidence['bayes_factor_combined']:.2f} ({combined_evidence['interpretation']})")

    # Salvar resultados
    output_path = os.path.join(base_dir, f"data/processed/integrated_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Resultados salvos em: {output_path}")

    return results

def _cross_validate_tracks(track_results: Dict) -> Dict:
    """Validação cruzada simples entre resultados dos tracks."""
    mass_evidence = track_results.get('mass_dependence', {}).get('bayesian_evidence', {}).get('interpretation', 'none')
    nonassoc_sig = any(res.get('significant_fdr', False) for res in
                      track_results.get('nonassociative_stats', {}).get('ks_test_results', {}).values())

    consistency = (
        ('strong' in mass_evidence or 'moderate' in mass_evidence) == nonassoc_sig
    )

    return {
        'mass_evidence_level': mass_evidence,
        'nonassoc_significant': nonassoc_sig,
        'overall_consistency': 'consistent' if consistency else 'inconsistent'
    }

def _compute_combined_bayes_factor(track_results: Dict) -> Dict:
    """Combina evidência Bayesiana dos três tracks (aproximação)."""
    bf_values = []

    # Track 1
    bf1 = track_results.get('mass_dependence', {}).get('bayesian_evidence', {}).get('bayes_factor_approx', 1.0)
    bf_values.append(bf1)

    # Track 2
    p2 = track_results.get('intention_correlation', {}).get('feature_results', {}).get('intention_score', {}).get('p_values', {}).get('fdr_pearson', 1.0)
    bf2 = -np.exp(1) * p2 * np.log(p2) if p2 > 0 and p2 < 1 else 1.0
    bf_values.append(bf2)

    # Track 3
    ks_results = track_results.get('nonassociative_stats', {}).get('ks_test_results', {})
    p3_vals = [res['p_values']['fdr'] for res in ks_results.values()]
    p3_min = min(p3_vals) if p3_vals else 1.0
    bf3 = -np.exp(1) * p3_min * np.log(p3_min) if p3_min > 0 and p3_min < 1 else 1.0
    bf_values.append(bf3)

    # Combinação multiplicativa
    bf_combined = np.prod(bf_values)

    if bf_combined > 100:
        interpretation = 'strong evidence for Orch‑OR/ARKHE convergence'
    elif bf_combined > 10:
        interpretation = 'moderate evidence'
    elif bf_combined > 3:
        interpretation = 'weak evidence'
    elif bf_combined < 0.1:
        interpretation = 'strong evidence against'
    else:
        interpretation = 'inconclusive'

    return {
        'individual_bayes_factors': [float(x) for x in bf_values],
        'bayes_factor_combined': float(bf_combined),
        'interpretation': interpretation
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/statistical_plan.json')
    args = parser.parse_args()
    results = run_integrated_experiment(args.config)
