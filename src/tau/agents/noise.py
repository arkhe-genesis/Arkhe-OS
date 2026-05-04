from typing import Any, Optional
import random
from .base import TAUAgent

class NoiseAgent(TAUAgent):
    """
    EPSILON (Ruído): NV-BFM / Explorador Caótico.
    Injeta distrações e explorações para evitar overfitting.
    """
    def __init__(self):
        super().__init__("EPSILON", "∇", "NV-BFM / Explorador Caótico")

    async def run_cycle(self, vacuum: Optional[Any] = None) -> bytes:
        if random.random() < 0.1:
            exploration_task = "Search for new free tier LLM APIs (OAM Exploration)."
            self.logger.info(f"Injecting noise: {exploration_task}")
            return self.qhttp_msg({"action": "EXPLORE", "task": exploration_task}, confidence=0.7)
        return self.qhttp_msg({"status": "IDLE_NOISE"}, confidence=1.0)
