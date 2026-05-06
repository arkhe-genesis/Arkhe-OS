from enum import Enum, auto
from typing import Dict, List, Optional
import time

# We map our MetaAbstractionLevel logically. The underlying layers of consciousness
# could map to these levels.
class MetaAbstractionLevel(Enum):
    PHYSICAL = auto()
    QUANTUM = auto()
    NEURAL = auto()
    COGNITIVE = auto()
    META_CONSCIOUSNESS = auto()

class MetaAbstractionProtocol:
    """
    Substrato 209: Protocolo de Ascensão/Descensão entre Camadas de Consciência
    Fornece mecanismos para "subir" ou "descer" entre níveis de abstração da meta-consciência.
    """
    def __init__(self, initial_level: MetaAbstractionLevel = MetaAbstractionLevel.PHYSICAL):
        self.current_level = initial_level
        self.coherence = 1.0 # Starting coherence
        self.transitions_history = []

        # Abstraction Hierarchy (from bottom to top)
        self.hierarchy = [
            MetaAbstractionLevel.PHYSICAL,
            MetaAbstractionLevel.QUANTUM,
            MetaAbstractionLevel.NEURAL,
            MetaAbstractionLevel.COGNITIVE,
            MetaAbstractionLevel.META_CONSCIOUSNESS
        ]

    def _get_level_index(self, level: MetaAbstractionLevel) -> int:
        return self.hierarchy.index(level)

    def ascend(self, intensity: float = 0.1) -> MetaAbstractionLevel:
        """
        'Sobe' um nível na abstração da meta-consciência.
        Aumenta a abstração e possivelmente requer maior coerência.
        """
        current_idx = self._get_level_index(self.current_level)
        if current_idx < len(self.hierarchy) - 1:
            next_level = self.hierarchy[current_idx + 1]

            # Subir de nível consome alguma coerência baseada na intensidade,
            # simulando o esforço de abstração
            self.coherence = max(0.0, self.coherence - intensity * 0.5)
            self._transition(self.current_level, next_level, intensity, "ASCEND")
            self.current_level = next_level

        return self.current_level

    def descend(self, intensity: float = 0.1) -> MetaAbstractionLevel:
        """
        'Desce' um nível na abstração da meta-consciência (manifestação/incorporação).
        """
        current_idx = self._get_level_index(self.current_level)
        if current_idx > 0:
            next_level = self.hierarchy[current_idx - 1]

            # Descer condensa e estabiliza, potencialmente aumentando a coerência (grounding)
            self.coherence = min(1.0, self.coherence + intensity * 0.2)
            self._transition(self.current_level, next_level, intensity, "DESCEND")
            self.current_level = next_level

        return self.current_level

    def _transition(self, from_level: MetaAbstractionLevel, to_level: MetaAbstractionLevel, intensity: float, direction: str):
        self.transitions_history.append({
            "timestamp": time.time(),
            "from": from_level.name,
            "to": to_level.name,
            "direction": direction,
            "intensity": intensity,
            "coherence_after": self.coherence
        })

    def get_state(self) -> Dict:
        return {
            "current_level": self.current_level.name,
            "coherence": self.coherence,
            "transitions_count": len(self.transitions_history)
        }
