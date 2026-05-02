#!/usr/bin/env python3
"""
run_crystal_brain_ising_execution.py
Executa pipeline Ising completo com benchmarking e preparação para ZEE200.
"""
import numpy as np
import json
import time
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from crystal_brain_ising_pipeline import (
    load_crystal_data, binarize_crystal_phases, fit_ising_crystal,
    detect_crystal_communities, classify_all_communities,
    validate_community_with_pca, run_crystal_brain_ising_analysis
)

def execute_full_pipeline(data_path=None, use_synthetic=True, n_timesteps=5000):
    print("🚀 ARKHE OS v∞.325.1 — Crystal Brain Ising Execution")
    print("=" * 75)

    execution_log = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'configuration': {
            'use_synthetic': use_synthetic,
            'n_timesteps': n_timesteps,
            'n_crystals': 768,
            'fingerprint': 0.58,
            'sync_phase': 0.58 * np.pi
        },
        'stages': {}
    }

    print("\n[STAGE 1/5] Loading/generating crystal phase data...")
    stage_start = time.perf_counter()

    if use_synthetic or data_path is None:
        from crystal_brain_ising_pipeline import generate_synthetic_crystal_data
        phases = generate_synthetic_crystal_data(n_timesteps=n_timesteps)
        print(f"   ✓ Generated synthetic data: {phases.shape}")
    else:
        phases = load_crystal_data(data_path)
        print(f"   ✓ Loaded real data: {phases.shape}")

    execution_log['stages']['data_loading'] = {
        'duration_s': time.perf_counter() - stage_start,
        'shape': list(phases.shape),
        'source': 'synthetic' if use_synthetic else 'real'
    }

    print("\n[STAGE 2/5] Binarizing phases to Ising codes...")
    stage_start = time.perf_counter()

    binarized = binarize_crystal_phases(phases)
    pos_ratio = np.mean(binarized == 1)

    print(f"   ✓ Binarized: {pos_ratio:.1%} active (+1), {1-pos_ratio:.1%} inactive (-1)")

    execution_log['stages']['binarization'] = {
        'duration_s': time.perf_counter() - stage_start,
        'positive_ratio': float(pos_ratio),
        'negative_ratio': float(1 - pos_ratio)
    }

    print("\n[STAGE 3/5] Fitting Ising model via pseudo-likelihood...")
    stage_start = time.perf_counter()

    J, h, log_lik = fit_ising_crystal(binarized, gamma=0.5, max_iter=500)

    non_zero = np.sum(np.abs(J) > 1e-8) // 2
    mean_abs_J = np.mean(np.abs(J[J != 0])) if non_zero > 0 else 0
    max_abs_J = np.max(np.abs(J))

    print(f"   ✓ Ising fitted: {non_zero} edges, mean|J|={mean_abs_J:.4f}, max|J|={max_abs_J:.4f}")
    print(f"   ✓ Log-likelihood: {log_lik:.2f}")

    execution_log['stages']['ising_fitting'] = {
        'duration_s': time.perf_counter() - stage_start,
        'n_edges': int(non_zero),
        'mean_abs_coupling': float(mean_abs_J),
        'max_abs_coupling': float(max_abs_J),
        'log_likelihood': float(log_lik),
        'sparsity': float(1 - non_zero / (768 * 767 / 2))
    }

    print("\n[STAGE 4/5] Detecting communities via Louvain...")
    stage_start = time.perf_counter()

    communities = detect_crystal_communities(J, resolution=1.0)

    community_sizes = [len(c) for c in communities.values()]

    print(f"   ✓ Detected {len(communities)} communities")
    print(f"   ✓ Size range: [{min(community_sizes)}, {max(community_sizes)}] crystals")
    print(f"   ✓ Mean size: {np.mean(community_sizes):.1f} ± {np.std(community_sizes):.1f}")

    execution_log['stages']['community_detection'] = {
        'duration_s': time.perf_counter() - stage_start,
        'n_communities': len(communities),
        'size_stats': {
            'min': min(community_sizes),
            'max': max(community_sizes),
            'mean': float(np.mean(community_sizes)),
            'std': float(np.std(community_sizes))
        }
    }

    print("\n[STAGE 5/5] Classifying regimes and validating...")
    stage_start = time.perf_counter()

    classification = classify_all_communities(J, communities, k_manifold_est=3, tau=0.3)

    regime_counts = {}
    for cid, info in classification.items():
        regime = info['regime']
        regime_counts[regime] = regime_counts.get(regime, 0) + 1

    print(f"\n📊 Regime distribution:")
    for regime, count in sorted(regime_counts.items()):
        print(f"   • {regime:12s}: {count:3d} communities")

    print(f"\n🔍 PCA validation (top 3 communities):")
    top_communities = sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)[:3]
    pca_results = {}

    for cid, crystals in top_communities:
        validation = validate_community_with_pca(binarized, crystals)
        pca_results[cid] = validation
        print(f"   Community {cid}: gap={validation['max_gap']:.3f}, "
              f"var_1d={validation['variance_explained_1d']:.1%}")

    execution_log['stages']['classification_validation'] = {
        'duration_s': time.perf_counter() - stage_start,
        'regime_distribution': regime_counts,
        'classification': classification,
        'pca_validation': {
            cid: {k: v for k, v in res.items() if k != 'eigenvalues_top10'}
            for cid, res in pca_results.items()
        }
    }

    print(f"\n🎯 Architectural recommendations:")
    recommendations = []

    if regime_counts.get('CAPTURE', 0) > 0:
        print("   ✅ CAPTURE detected: maintain current sparsity, explore manifold steering")
        recommendations.append({
            'regime': 'CAPTURE',
            'action': 'maintain_sparsity',
            'next_step': 'explore_steering_along_manifold'
        })

    if regime_counts.get('SHATTERING', 0) > 0:
        print("   ⚠️  SHATTERING detected: consider increasing global coupling κ")
        recommendations.append({
            'regime': 'SHATTERING',
            'action': 'increase_coupling',
            'next_step': 'evaluate_fragmentation_for_use_case'
        })

    if regime_counts.get('DILUTION', 0) > len(communities) * 0.5:
        print("   ❌ DILUTION dominant: increase SAE sparsity or adjust binarization threshold")
        recommendations.append({
            'regime': 'DILUTION',
            'action': 'increase_sparsity_or_adjust_threshold',
            'next_step': 'retrain_sae_with_stronger_l1'
        })

    execution_log['recommendations'] = recommendations

    capture_communities = [
        cid for cid, info in classification.items()
        if info['regime'] == 'CAPTURE'
    ]

    if capture_communities:
        print(f"\n🔐 ZEE200 integration: {len(capture_communities)} CAPTURE communities identified")
        print(f"   Ready for subspace capture proof generation")
        execution_log['zee200_ready'] = {
            'capture_communities': capture_communities,
            'manifold_dimension_est': 3,
            'epsilon_target': 0.01
        }
    else:
        print(f"\n⚠️  No CAPTURE communities found — ZEE200 proof requires regime adjustment")
        execution_log['zee200_ready'] = None

    Path('results').mkdir(exist_ok=True)
    output_path = 'results/crystal_brain_ising_execution_v325_1.json'
    with open(output_path, 'w') as f:
        json.dump(execution_log, f, indent=2)

    print(f"\n💾 Execution log saved: {output_path}")

    if use_synthetic or data_path is None:
        Path('data').mkdir(exist_ok=True)
        np.save('data/crystal_brain_v15_binarized.npy', binarized)
        np.save('data/crystal_brain_v15_J.npy', J)
        print(f"💾 Synthetic matrices saved in data/ directory")

    return execution_log

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=None, help="Caminho para dados reais")
    args = parser.parse_args()

    use_synth = args.data is None
    log = execute_full_pipeline(data_path=args.data, use_synthetic=use_synth, n_timesteps=5000)
    print(f"\n✅ Pipeline execution complete. Total time: {sum(s['duration_s'] for s in log['stages'].values()):.2f}s")
