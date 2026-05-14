import numpy as np
from dataclasses import dataclass

@dataclass
class ThreatSignature:
    category: str
    pattern: str
    embedding_anchor: np.ndarray
    severity: float
    description: str

class ThreatDatabase:
    def __init__(self):
        self.signatures = []

    def match_embedding(self, embedding: np.ndarray, threshold: float = 0.85) -> bool:
        if not self.signatures:
            return False
        # Mock matching
        return np.random.random() > 0.8

    def add_signature(self, signature: ThreatSignature):
        self.signatures.append(signature)
