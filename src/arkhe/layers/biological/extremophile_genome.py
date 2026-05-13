from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ExtremophileGenome:
    id: str
    name: str
    type: str  # e.g., 'thermophile', 'radiophile', 'halophile'
    sequence: Optional[str] = None
    junk_percentage: float = 0.0
    ecc_mechanisms: List[str] = field(default_factory=list)
    rad_resistance: float = 0.0  # arbitrary score or measure
    go_annotations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "sequence": self.sequence,
            "junk_percentage": self.junk_percentage,
            "ecc_mechanisms": self.ecc_mechanisms,
            "rad_resistance": self.rad_resistance,
            "go_annotations": self.go_annotations
        }
