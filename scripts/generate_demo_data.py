#!/usr/bin/env python3
"""
generate_demo_data.py
Gera dados sintéticos realistas para validar pipeline GTZK sem hardware real.
"""
import numpy as np
import json
from pathlib import Path

def generate_track1_demo_data(output_path='results/track1_raw.json'):
    """Gera dados sintéticos para Track 1: scaling de massa."""
    np.random.seed(42)

    # Configurações de grid (massa efetiva M = N²)
    grid_sizes = [16, 24, 32, 48, 64, 96]
    n_trials_per_N = 15

    results = []
    for N in grid_sizes:
        M = N**2
        # Modelo Orch-OR: τ = a/√M + b + ruído
        a_true, b_true = 112.3, 1.61  # Valores de referência
        taus = []
        for _ in range(n_trials_per_N):
            tau = a_true / np.sqrt(M) + b_true + np.random.normal(0, 0.3)
            taus.append(max(0.1, tau))  # τ > 0

        results.append({
            'N': N,
            'M': M,
            'mean_tau': float(np.mean(taus)),
            'std_tau': float(np.std(taus)),
            'n_trials': n_trials_per_N,
            'all_taus': [float(t) for t in taus]
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'grid_sizes': grid_sizes, 'measurements': results}, f, indent=2)

    print(f"✓ Track 1 demo data: {output_path}")
    return results

def generate_track2_demo_data(output_path='results/track2_raw.json'):
    """Gera dados sintéticos para Track 2: acoplamento informacional."""
    np.random.seed(43)
    n_trials = 100

    # Sinais de intenção [0, 1]
    intention = np.random.uniform(0, 1, n_trials)

    # Modelo de sensor: leitura = sigmoid(intenção × força) + ruído
    strength = 0.8
    sat_scale, noise_std = 1.0, 0.05
    predicted = 2.0 / (1.0 + np.exp(-np.clip(intention * strength / sat_scale, -5, 5))) - 1.0
    sensor_readings = predicted + np.random.normal(0, noise_std, n_trials)

    data = {
        'intention_signals': intention.tolist(),
        'sensor_readings': sensor_readings.tolist(),
        'sensor_params': {'saturation_scale': sat_scale, 'noise_std': noise_std},
        'n_trials': n_trials
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Track 2 demo data: {output_path}")
    return data

def generate_track3_demo_data(output_path='results/track3_raw.json', grid_size=48):
    """Gera dados sintéticos para Track 3: associador octoniônico."""
    np.random.seed(44)
    N = grid_size * grid_size

    # Campos de velocidade/pressão sintéticos
    u = np.random.randn(N) * 0.1
    v = np.random.randn(N) * 0.1
    p = np.random.randn(N) * 0.05

    data = {
        'velocity_fields': {'u': u.tolist(), 'v': v.tolist()},
        'pressure_field': p.tolist(),
        'grid_size': grid_size,
        'n_points': N
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Track 3 demo data: {output_path}")
    return data

if __name__ == '__main__':
    generate_track1_demo_data()
    generate_track2_demo_data()
    generate_track3_demo_data()
    print("\n🎯 Dados de exemplo gerados. Pronto para pipeline GTZK.")
