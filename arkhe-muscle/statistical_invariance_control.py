# statistical_invariance_control.py — Controle estatístico de invariância
import numpy as np

class SPCInvariance:
    def __init__(self, target_cpk=2.0):
        self.target_cpk = target_cpk
    def compute_cpk(self, errors):
        std = np.std(errors)
        if std == 0: return 2.0
        return (1e-6 - np.mean(errors)) / (3 * std)

if __name__ == "__main__":
    spc = SPCInvariance()
    errors = np.random.normal(7e-7, 1e-7, 100)
    print(f"Cpk calculado: {spc.compute_cpk(errors):.4f}")
