from typing import Any, Optional
from .base import TAUAgent
import time

class GuardianAgent(TAUAgent):
    """
    ALFA (Guardião): Mesh Controller / TP53.
    Monitora a saúde do enxame e aplica Histerese.
    """
    def __init__(self):
        super().__init__("ALFA", "Ω", "Mesh Controller / TP53")
        self.threshold = 0.65 # ARKHE-N Certified v1.1

    async def run_cycle(self, vacuum: Optional[Any] = None) -> bytes:
        if vacuum:
            new_lambda = self.compute_lambda_mesh(vacuum)
            vacuum.set_coherence(new_lambda)
            self.observe(new_lambda)

        hysteresis = self.get_hysteresis()
        self.logger.info(f"Checking mesh health: λ={self.lambda_mesh:.4f}, H={hysteresis:.4f}")

        if hysteresis < self.threshold:
            self.logger.warning("COHERENCE CRITICAL: Initiating stabilization protocol.")
            return self.qhttp_msg({"action": "STABILIZE", "target": "global"}, confidence=0.99)

        return self.qhttp_msg({"status": "HEALTHY", "lambda": self.lambda_mesh}, confidence=1.0)

    def compute_lambda_mesh(self, vacuum: Any) -> float:
        """
        Fórmula ARKHE: Λ = 0.5*online_ratio + 0.3*success + 0.2*(1/latency_norm)
        """
        metrics = vacuum.get_metrics()
        agents = vacuum.live_state.get("agents", {})

        # 1. Online Ratio
        total_agents = 12 # Dodecarchy
        online_agents = sum(1 for a in agents.values() if a.get("status") == "online")
        online_ratio = online_agents / total_agents

        # 2. Success Rate
        success = metrics.get("success_rate", 1.0)

        # 3. Latency Norm (assuming 1000ms as baseline)
        avg_latency = metrics.get("avg_latency_ms", 100.0)
        latency_norm = max(1.0, avg_latency / 100.0)

        new_lambda = (0.5 * online_ratio) + (0.3 * success) + (0.2 * (1.0 / latency_norm))
        return min(1.0, max(0.0, new_lambda))
