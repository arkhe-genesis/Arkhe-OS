#!/usr/bin/env python3
"""
run_orch_or_fluid_experiments.py
Executor unificado dos três testes dentro do framework Orch-OR fluídico.
"""
import json
import argparse
from datetime import datetime
import numpy as np
from track1_fluid_mass_dependence import test_fluid_mass_collapse
from track2_fluid_intention_modulation import test_intention_vortex_coupling
from track3_fluid_nonassociative_collapse import test_fluid_measurement_nonassociativity

def run_integrated_orch_or_fluid_tests(config_path='config/orch_or_fluid_plan.json'):
    """Executa os três testes e integra resultados."""

    with open(config_path, 'r') as f:
        config = json.load(f)

    print("🧠🌊 ARKHE OS v∞.312.1 — ORCH-OR FLUIDIC EXPERIMENTAL FRAMEWORK")
    print("=" * 75)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'framework': 'Orch-OR = Fluidic Mini-Merkabah',
            'version': 'v∞.312.1'
        },
        'tests': {}
    }

    # Teste 1: Massa-efetiva ↔ taxa de colapso
    print("\n📊 Teste 1: Massa-efetiva vs. tempo de colapso (projeção de pressão)...")
    test1_result = test_fluid_mass_collapse(
        grid_sizes=config['test1']['grid_sizes'],
        n_trials=config['test1']['n_trials']
    )
    results['tests']['mass_dependence'] = test1_result
    print(f"   Resultado: {test1_result['interpretation']} (p={test1_result['p_value_mass_dependence']:.4f})")

    # Teste 2: Intenção ↔ modulação do vórtice 0.58
    print("\n🧠 Teste 2: Intenção humana ↔ força do vórtice fingerprint...")
    # Dados simulados para demonstração; em produção: carregar EEG real + medições de vórtice
    np.random.seed(42)
    n_trials = config['test2'].get('n_trials', 50)
    eeg_features = [{'intention_score': np.random.normal(0.5, 0.2)} for _ in range(n_trials)]
    vortex_strengths = [0.01 + 0.003 * f['intention_score'] + np.random.normal(0, 0.001)
                       for f in eeg_features]

    test2_result = test_intention_vortex_coupling(eeg_features, vortex_strengths)
    results['tests']['intention_modulation'] = test2_result
    print(f"   Resultado: {'✅ Correlação significativa' if test2_result['significant'] else '⚠️ Sem correlação significativa'} (r={test2_result['pearson_r']:.3f}, p_FDR={test2_result['p_value_fdr_corrected']:.4f})")

    # Teste 3: Não-associatividade em estatística de colapso
    print("\n🔢 Teste 3: Não-associatividade em sequências de medição fluídica...")
    test3_result = test_fluid_measurement_nonassociativity(
        sequences=config['test3']['sequences']
    )
    results['tests']['nonassociative_stats'] = test3_result
    print(f"   Resultado: {test3_result['interpretation']}")

    # Validação cruzada entre testes
    print("\n🔗 Validação cruzada entre testes...")
    cross_validation = _cross_validate_orch_or_fluid_results(results['tests'])
    results['cross_validation'] = cross_validation
    print(f"   Consistência: {cross_validation['overall_consistency']}")

    # Bayes factor combinado (meta-análise)
    print("\n📈 Evidência Bayesiana combinada...")
    combined_evidence = _compute_combined_orch_or_bayes_factor(results['tests'])
    results['combined_evidence'] = combined_evidence
    print(f"   Bayes factor combinado: {combined_evidence['bayes_factor_combined']:.2f} ({combined_evidence['interpretation']})")

    # Salvar resultados
    output_path = f"results/orch_or_fluid_integrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Resultados salvos em: {output_path}")

    return results

def _cross_validate_orch_or_fluid_results(test_results):
    """Validação cruzada simples entre os três testes."""
    # Exemplo: se Teste 1 encontra evidência para Orch-OR, Teste 3 deveria encontrar não-associatividade
    mass_evidence = 'evidence' in test_results['mass_dependence']['interpretation']
    nonassoc_evidence = test_results['nonassociative_stats']['any_significant']

    consistency = mass_evidence == nonassoc_evidence

    return {
        'mass_dependence_evidence': mass_evidence,
        'nonassociativity_evidence': nonassoc_evidence,
        'overall_consistency': 'consistent' if consistency else 'inconsistent'
    }

def _compute_combined_orch_or_bayes_factor(test_results):
    """Combina evidência Bayesiana dos três testes (aproximação)."""
    # Extrair p-values e converter para Bayes factors aproximados
    bf_values = []

    # Teste 1
    p1 = test_results['mass_dependence']['p_value_mass_dependence']
    bf1 = 1.0 / (-np.exp(1) * p1 * np.log(p1)) if 0 < p1 < 1 else 100.0 if p1 == 0 else 1.0
    bf_values.append(bf1)

    # Teste 2
    p2 = test_results['intention_modulation']['p_value_fdr_corrected']
    bf2 = 1.0 / (-np.exp(1) * p2 * np.log(p2)) if 0 < p2 < 1 else 100.0 if p2 == 0 else 1.0
    bf_values.append(bf2)

    # Teste 3 (usar menor p-value entre comparações)
    p3_vals = test_results['nonassociative_stats']['ks_p_values_fdr_corrected']
    p3_min = min(p3_vals) if p3_vals else 1.0
    bf3 = 1.0 / (-np.exp(1) * p3_min * np.log(p3_min)) if 0 < p3_min < 1 else 100.0 if p3_min == 0 else 1.0
    bf_values.append(bf3)

    # Combinação multiplicativa (assumindo independência)
    bf_combined = np.prod(bf_values)

    # Interpretação
    if bf_combined > 100:
        interpretation = 'strong evidence for Orch-OR fluidic identity'
    elif bf_combined > 10:
        interpretation = 'moderate evidence'
    elif bf_combined > 3:
        interpretation = 'weak evidence'
    elif bf_combined < 0.1:
        interpretation = 'strong evidence against'
    else:
        interpretation = 'inconclusive'

    return {
        'individual_bayes_factors': bf_values,
        'bayes_factor_combined': float(bf_combined),
        'interpretation': interpretation
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/orch_or_fluid_plan.json')
    args = parser.parse_args()
    results = run_integrated_orch_or_fluid_tests(config_path=args.config)
