# ghost_threshold_validator.py — Substrato 824.1-FASE1
# Simula carga em cluster K8s até colapso de coerência

import random
import math
from dataclasses import dataclass

@dataclass
class PodState:
    name: str
    phase: float  # θ ∈ [0, 2π)
    healthy: bool
    latency_ms: float

class K8sCoherenceSimulator:
    def __init__(self, n_pods: int, base_latency: float = 50.0):
        self.pods = [
            PodState(
                name="pod-" + str(i),
                phase=0.0,  # inicialmente sincronizados
                healthy=True,
                latency_ms=base_latency
            )
            for i in range(n_pods)
        ]
        self.failure_rate = 0.0

    def inject_chaos(self, failure_rate: float, latency_spike: float):
        """Simula degradação: pods falham, latência sobe."""
        self.failure_rate = failure_rate
        for pod in self.pods:
            if random.random() < failure_rate:
                pod.healthy = False
                pod.phase = random.uniform(0, 2 * math.pi)  # desincronização
                pod.latency_ms *= random.uniform(2.0, latency_spike)

    def compute_order_parameter(self) -> float:
        """r = |(1/N) Σ exp(iθ_j)| considerando apenas pods saudáveis."""
        healthy = [p for p in self.pods if p.healthy]
        if not healthy:
            return 0.0

        n = len(healthy)
        real = sum(math.cos(p.phase) for p in healthy)
        imag = sum(math.sin(p.phase) for p in healthy)
        return ((real**2 + imag**2) ** 0.5) / n

    def run_experiment(self, max_load: int) -> dict:
        """Escala carga até detectar colapso (r < 0.577)."""
        results = []
        for load in range(100, max_load + 1, 100):
            # Cada 100 unidades de load = +5% failure rate
            failure = min(load / 2000, 0.95)
            self.inject_chaos(failure, latency_spike=10.0)
            r = self.compute_order_parameter()
            results.append({
                "load": load,
                "failure_rate": failure,
                "r": r,
                "collapsed": r < 0.577,
                "healthy_pods": sum(1 for p in self.pods if p.healthy)
            })
            if r < 0.577:
                break
        return results

if __name__ == "__main__":
    # Execução
    sim = K8sCoherenceSimulator(n_pods=100)
    experiment = sim.run_experiment(max_load=5000)

    print("╔════════════════════════════════════════════╗")
    print("║   GHOST THRESHOLD VALIDATION (824.1-F1)   ║")
    print("╚════════════════════════════════════════════╝")
    for r in experiment:
        status = "💥 COLAPSO" if r["collapsed"] else "✓ COERENTE"
        print("Load " + str(r['load']).rjust(5) + " | Fail " + "{:.2f}%".format(r['failure_rate'] * 100) + " | r=" + "{:.4f}".format(r['r']) + " | Healthy=" + str(r['healthy_pods']).rjust(3) + "/100 " + status)
