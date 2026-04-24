# quantum_processor.py — Mock do Processador Quântico

import logging

class QuantumProcessor:
    """Mock do Processador Quântico para testes de caos."""

    def __init__(self, name: str = "qproc-0"):
        self.name = name
        self.fidelity = 0.999
        self.ready = True

    def simulate_degradation(self, fidelity: float):
        self.fidelity = fidelity
        logging.warning(f"[Quantum] Fidelidade degradada para {fidelity:.4f}")

    def is_ready(self) -> bool:
        return self.ready and self.fidelity > 0.90
