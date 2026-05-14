from dataclasses import dataclass, field
from typing import Dict, Any
from .extremophile_analyzer import ExtremophileGenome

@dataclass
class ECCParams:
    n: int
    k: int
    t: int = field(init=False)

    def __post_init__(self):
        self.t = (self.n - self.k) // 2

    def validate(self) -> bool:
        return True

# Map RSParameters to ECCParams to resolve import
RSParameters = ECCParams

class AdaptiveGenomicECC:
    def configure_for_organism(self, genome: ExtremophileGenome, params: Dict[str, Any]) -> ECCParams:
        # Dummy configuration for testing
        return ECCParams(n=255, k=223)
