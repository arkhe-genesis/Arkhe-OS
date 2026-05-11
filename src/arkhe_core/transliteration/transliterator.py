import numpy as np
from typing import List, Dict, Any, Tuple
import time

from .algebra import Clifford4D
from .synthesis import SyntheticCore
from .coherence import CoherenceEnforcer
from .cohesion import CohesionGuardian
from .dependencies import K6O_Cathedral, QNode

class TransliterationFailure(Exception):
    """Lançado quando o processo de transliteração falha globalmente."""
    pass

class ArkheTransliterator:
    """
    Motor de transliteração artificial completo.
    Aplica as Três Leis (Síntese, Coerência, Coesão) a todo dado que atravessa substratos.
    """

    def __init__(self, k6o_network: K6O_Cathedral, qnode: QNode):
        self.cl = Clifford4D()
        self.synthesis = SyntheticCore(self.cl)
        self.coherence = CoherenceEnforcer(k6o_network)
        self.cohesion = CohesionGuardian(qnode)
        self.history: List[Dict] = []

    def transmute(self,
                 payload: np.ndarray,
                 source_substrate: str,
                 target_substrate: str,
                 source_phase: float,
                 source_features: List[str],
                 target_features: List[str],
                 mapping: Dict[str, str]) -> Tuple[np.ndarray, float]:
        """
        Translitera payload do substrato source para target, validando as Três Leis.
        """
        # 1. SÍNTESE
        target_baseline = np.zeros(self.cl.total_size)
        phi = self.synthesis.fuse(payload, target_baseline)

        # 2. COERÊNCIA
        phi_coherent, target_phase = self.coherence.transliterate(
            phi, source_phase, target_substrate
        )

        # 3. COESÃO
        G_source = self.cohesion.extract_causal_graph(payload, source_features)
        G_target = self.cohesion.extract_causal_graph(phi_coherent, target_features)

        if not self.cohesion.verify_cohesion(G_source, G_target, mapping):
            raise TransliterationFailure("Lei da Coesão violada no estágio final")

        # Registro
        arkhe_number = self._compute_arkhe_number(phi_coherent, target_phase, G_source, G_target, mapping)

        self.history.append({
            'timestamp': time.time(),
            'source': source_substrate,
            'target': target_substrate,
            'arkhe_number': arkhe_number,
            'synthesis_entropy': self.synthesis.synthetic_entropy(phi_coherent)
        })

        return phi_coherent, target_phase

    def _compute_arkhe_number(self, phi, phase, G_src, G_tgt, mapping) -> float:
        """Calcula o invariante de transliteração (Arkhe Number)."""
        H = self.synthesis.synthetic_entropy(phi)
        C = np.abs(np.exp(1j * phase))
        W = self.cohesion.causal_wasserstein(G_src, G_tgt, mapping)

        return 0.4 * H + 0.3 * (1 - C) + 0.3 * W
