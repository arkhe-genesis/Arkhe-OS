#!/usr/bin/env python3
"""
initialize_array.py — Inicializa array de cristais para trial com seed específico.
"""
import numpy as np
import json

class MerkabahController:
    """Mock do hardware controller para inicialização"""
    def __init__(self, grid_size):
        self.N = grid_size
        self.phases = None

    def apply_phases(self, phases):
        self.phases = phases

    def wait_for_settling(self, timeout):
        pass # mock

    def measure_order_parameter(self):
        if self.phases is None:
            return 0.0
        return np.abs(np.mean(np.exp(1j * self.phases)))

    def measure_rms_divergence(self):
        if self.phases is None:
            return 1.0
        return float(np.std(self.phases) * 0.1) # mock value

def initialize_for_trial(N, trial_id, seed, target_coherence=0.3):
    """Prepara array de tamanho N para trial com seed e coerência alvo."""

    # Instanciar controlador
    ctrl = MerkabahController(grid_size=N)

    # Gerar fases iniciais com coerência parcial
    np.random.seed(seed)
    sync_phase = 0.58 * np.pi
    dispersion = np.arccos(2 * target_coherence - 1)
    phases = np.random.vonmises(sync_phase, 1/dispersion, N*N) % (2*np.pi)

    # Aplicar fases ao hardware
    ctrl.apply_phases(phases)

    # Aguardar estabilização
    ctrl.wait_for_settling(timeout=30)  # 30 segundos máximo

    # Verificar estado inicial
    initial_r = ctrl.measure_order_parameter()
    initial_div = ctrl.measure_rms_divergence()

    return {
        'N': N,
        'trial_id': trial_id,
        'seed': seed,
        'initial_coherence': float(initial_r),
        'initial_divergence': float(initial_div),
        'ready_for_measurement': True
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print("Usage: python initialize_array.py <N> <trial_id> <seed>")
        sys.exit(1)

    N = int(sys.argv[1])
    trial_id = int(sys.argv[2])
    seed = int(sys.argv[3])

    result = initialize_for_trial(N, trial_id, seed)
    print(json.dumps(result, indent=2))
