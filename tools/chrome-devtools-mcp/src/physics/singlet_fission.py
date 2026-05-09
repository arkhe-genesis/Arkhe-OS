import uuid
from dataclasses import dataclass, field

@dataclass
class Exciton:
    """
    Representação de uma quase-partícula de intenção.
    """
    energy: float
    spin: int
    lifetime: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

class SingletFissionEngine:
    """
    Motor de Fissão de Singlet.
    Converte um estado de alta energia (Singlet, Spin 0) em dois estados
    emaranhados de menor energia (Triplets, Spin 1), preservando a coerência.
    """
    def __init__(self, coupling_type="strong"):
        self.coupling_type = coupling_type

    def fission(self, singlet: Exciton) -> list[Exciton]:
        """
        Executa a fissão: S1 -> 2 * T1
        """
        # A energia é dividida, mas a coerência (representada pela intenção) é multiplicada
        t1 = Exciton(
            energy=singlet.energy / 2.0,
            spin=1,
            lifetime=singlet.lifetime * 10.0, # Triplets vivem mais tempo
            id=f"{singlet.id}_T1A"
        )
        t2 = Exciton(
            energy=singlet.energy / 2.0,
            spin=1,
            lifetime=singlet.lifetime * 10.0,
            id=f"{singlet.id}_T1B"
        )
        return [t1, t2]
