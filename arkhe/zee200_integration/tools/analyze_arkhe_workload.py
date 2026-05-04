#!/usr/bin/env python3
"""
tools/analyze_arkhe_workload.py
Analisa distribuição de recursos no workload ARKHE para tuning de profile.
"""
import json
import numpy as np
from pathlib import Path

def analyze_arkhe_resource_usage(benchmark_results_path: str):
    """Analisa uso de recursos (uin, uset, ukvs, u×) nos benchmarks ARKHE."""

    with open(benchmark_results_path) as f:
        data = json.load(f)

    # Extrair métricas de uso de recursos por instrução GTZK
    resource_usage = {
        'track1': {'uin': 0, 'uset': 0, 'ukvs': 0, 'ux': 0, 'count': 0},
        'track2': {'uin': 0, 'uset': 0, 'ukvs': 0, 'ux': 0, 'count': 0},
        'track3': {'uin': 0, 'uset': 0, 'ukvs': 0, 'ux': 0, 'count': 0},
    }

    for result in data['raw_results']:
        track = result['track']
        opt = result['optimizations']

        # Estimativa baseada em análise estática dos gadgets
        if track == 'track1':
            # Curve fit: ~45 field mults, ~12 set lookups, ~8 aux inputs
            resource_usage[track]['ux'] += 45
            resource_usage[track]['uset'] += 12
            resource_usage[track]['uin'] += 8
            resource_usage[track]['count'] += 1

        elif track == 'track2':
            # MI estimator: depende de mi_bins
            bins = opt.get('mi_bins', 40)
            # ~120 field mults, ~2*bins set lookups, ~40 aux inputs
            resource_usage[track]['ux'] += 120
            resource_usage[track]['uset'] += 2 * bins
            resource_usage[track]['uin'] += 40
            resource_usage[track]['count'] += 1

        elif track == 'track3':
            # Associator: depende de sample_rate
            sample = opt.get('sample_rate', 1.0)
            # ~84 field mults, ~24*sample kvs lookups, ~6 aux inputs
            resource_usage[track]['ux'] += 84
            resource_usage[track]['ukvs'] += int(24 * sample)
            resource_usage[track]['uin'] += 6
            resource_usage[track]['count'] += 1

    # Calcular médias por track
    averages = {}
    for track, usage in resource_usage.items():
        if usage['count'] > 0:
            averages[track] = {
                'avg_uin': usage['uin'] / usage['count'],
                'avg_uset': usage['uset'] / usage['count'],
                'avg_ukvs': usage['ukvs'] / usage['count'],
                'avg_ux': usage['ux'] / usage['count'],
            }

    # Calcular profile ótimo via minimização de padding overhead
    # Objetivo: minimizar max(ceil(n_in/uin), ceil(n_set/uset), ...)
    def compute_padding_overhead(profile, usage):
        uin, uset, ukvs, ux = profile
        overhead = 0
        for track, avg in usage.items():
            if avg['avg_ux'] > 0:
                units = max(
                    np.ceil(avg['avg_uin'] / uin) if uin > 0 else 1e9,
                    np.ceil(avg['avg_uset'] / uset) if uset > 0 else 1e9,
                    np.ceil(avg['avg_ukvs'] / ukvs) if ukvs > 0 else 1e9,
                    np.ceil(avg['avg_ux'] / ux) if ux > 0 else 1e9,
                )
                # Padding = units * profile - actual usage
                padding = (
                    units * uin - avg['avg_uin'] +
                    units * uset - avg['avg_uset'] +
                    units * ukvs - avg['avg_ukvs'] +
                    units * ux - avg['avg_ux']
                )
                overhead += padding
        return overhead

    # Testar profiles candidatos
    candidate_profiles = [
        (1, 1, 1, 1),  # Uniforme (baseline)
        (1, 2, 1, 2),  # Mais uset/ux (para Track 2)
        (1, 1, 2, 2),  # Mais ukvs/ux (para Track 3)
        (2, 2, 1, 2),  # Mais uin/uset/ux
    ]

    print("🔍 Analyzing ARKHE workload for optimal universal-unit profile...")
    print(f"{'Profile':<20} {'Padding Overhead':>20} {'Recommendation':>15}")
    print("-" * 60)

    best_profile = None
    best_overhead = float('inf')

    for profile in candidate_profiles:
        overhead = compute_padding_overhead(profile, averages)
        recommendation = "✓ BEST" if overhead < best_overhead else ""
        if overhead < best_overhead:
            best_overhead = overhead
            best_profile = profile
        print(f"{str(profile):<20} {overhead:>20.1f} {recommendation:>15}")

    print(f"\n✅ Recommended profile: {best_profile}")
    print(f"   Expected padding reduction: {(compute_padding_overhead((1,1,1,1), averages) - best_overhead) / compute_padding_overhead((1,1,1,1), averages) * 100:.1f}%")

    return best_profile, averages

if __name__ == '__main__':
    profile, averages = analyze_arkhe_resource_usage('results/benchmarks/comparative_v320_4.json')
    print(f"\n📝 Update ZEE200 config: universal_unit_profile = {profile}")
