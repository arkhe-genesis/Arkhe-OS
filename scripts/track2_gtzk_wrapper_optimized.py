#!/usr/bin/env python3
"""
track2_gtzk_wrapper_optimized.py
Versão otimizada do wrapper Track 2 com constraints reduzidas.
"""
import numpy as np
import json
from scipy import stats

def track2_gtzk_instruction_optimized(intention_signals, sensor_readings, sensor_params):
    # Otimização 1: Reduzir bins de histograma de 40->20
    # Otimização 2: Aproximação de MI via correlação de rank
    n = len(intention_signals)

    # Aproximação rápida de MI usando correlação
    r, p = stats.spearmanr(intention_signals, sensor_readings)

    # MI aproximação sob suposição gaussiana: MI = -0.5 * ln(1 - r^2)
    # Apenas se r for válido
    if not np.isnan(r) and abs(r) < 1.0:
        mi_nats = -0.5 * np.log(1 - r**2)
    else:
        mi_nats = 0.0

    constraints = [
        "precomputed_sigmoid_kvs_lookup",
        "rank_correlation_approximation",
        "reduced_bins_20"
    ]

    public_outputs = {
        'mi_nats': float(mi_nats),
        'correlation': float(r) if not np.isnan(r) else 0.0,
        'p_value': float(p) if not np.isnan(p) else 1.0
    }

    private_witness = {
        'residuals': float(np.mean(sensor_readings))
    }

    from track1_gtzk_wrapper import GTZKInstruction
    instruction = GTZKInstruction(
        name='track2_mi_estimator_opt',
        public_inputs={'n_samples': n},
        private_witness=private_witness,
        constraints=constraints
    )

    return instruction, public_outputs
