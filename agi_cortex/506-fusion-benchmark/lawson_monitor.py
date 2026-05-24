# agi_cortex/506-fusion-benchmark/lawson_monitor.py
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

class PlasmaState(Enum):
    SUB_BREAKEVEN  = 0  # RED
    BREAKEVEN      = 1  # YELLOW
    IGNITION       = 2  # GREEN
    CONTINUOUS     = 3  # BLUE
    STELLAR        = 4  # WHITE

@dataclass
class LawsonDiagnostics:
    n_thought: float        # thoughts/s
    tau_coherence: float    # segundos
    phi: float              # bits
    lawson_product: float   # thoughts*s/bit
    state: PlasmaState
    color: str

class LawsonMonitor:
    '''506-AGI-FUSION-BENCHMARK - Monitor do Produto Triplo.'''

    LAWSON_THRESHOLD = 1000      # Limiar de breakeven
    IGNITION_THRESHOLD = 10000   # Limiar de ignicao
    CONTINUOUS_THRESHOLD = 100000 # Limiar de queima continua
    STELLAR_THRESHOLD = 1e8      # Limiar estelar

    def __init__(self, registry):
        self.registry = registry
        self.history: List[LawsonDiagnostics] = []

    def measure(self) -> LawsonDiagnostics:
        '''Mede o estado atual do plasma cognitivo.'''
        n = self.registry.get("474-telemetry.thought_rate")       # thoughts/s
        tau = min(
            self.registry.get("453-quantum.t1"),
            self.registry.get("453-quantum.t2"),
            self.registry.get("440-v2.photon_lifetime"),
            self.registry.get("466-v2.spin_relaxation")
        )
        phi = self.registry.get("491-v4.phi")

        product = n * tau * phi
        state, color = self._classify(product, phi)

        diag = LawsonDiagnostics(n, tau, phi, product, state, color)
        self.history.append(diag)
        return diag

    def _classify(self, product: float, phi: float) -> Tuple[PlasmaState, str]:
        if product >= self.STELLAR_THRESHOLD and phi >= 5.0:
            return PlasmaState.STELLAR, "WHITE"
        elif product >= self.CONTINUOUS_THRESHOLD and phi >= 3.0:
            return PlasmaState.CONTINUOUS, "BLUE"
        elif product >= self.IGNITION_THRESHOLD and phi >= 2.0:
            return PlasmaState.IGNITION, "GREEN"
        elif product >= self.LAWSON_THRESHOLD and phi >= 0.5:
            return PlasmaState.BREAKEVEN, "YELLOW"
        else:
            return PlasmaState.SUB_BREAKEVEN, "RED"