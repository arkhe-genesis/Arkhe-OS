from dataclasses import dataclass, field
from typing import List

@dataclass
class IntelligenceProposition:
    statement: str
    evidence_hashes: List[str]
    confidence: float
    analyst_id: str

class LeanToBeaver:
    def convert(self, lean_spec: str) -> IntelligenceProposition:
        return IntelligenceProposition(
            statement=lean_spec,
            evidence_hashes=["hash1"],
            confidence=0.98,
            analyst_id="lean_bridge"
        )
