import abc
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from src.tau.core.qhttp import QHTTPProtocol

class TAUAgent(abc.ABC):
    """
    Base class for TAU Dodecarchy Agents (v1.1).
    Follows qhttp semantics and EQBE compliance.
    """
    def __init__(self, agent_id: str, symbol: str, role: str):
        self.agent_id = agent_id
        self.symbol = symbol
        self.role = role
        self.lambda_mesh = 1.0
        self.last_observation = time.time()
        self.history: List[float] = []
        self.logger = logging.getLogger(f"TAU-{self.agent_id}")
        self.protocol = QHTTPProtocol()

    def qhttp_msg(self, payload: Any, confidence: float = 1.0) -> bytes:
        """Wraps a payload in a qhttp message (binary)."""
        return self.protocol.wrap(self.agent_id, self.symbol, payload, confidence)

    def get_hysteresis(self) -> float:
        if not self.history:
            return 1.0 # Inicialmente coerente
        return sum(self.history[-4:]) / max(len(self.history[-4:]), 1)

    @abc.abstractmethod
    async def run_cycle(self, vacuum: Optional[Any] = None) -> bytes:
        pass

    def observe(self, lambda_val: float):
        self.lambda_mesh = lambda_val
        self.history.append(lambda_val)
        if len(self.history) > 100:
            self.history.pop(0)
        self.last_observation = time.time()
