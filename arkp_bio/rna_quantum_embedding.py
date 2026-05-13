import numpy as np
from enum import Enum, auto
from dataclasses import dataclass

class RNAType(Enum):
    mRNA = auto()
    tRNA = auto()
    rRNA = auto()
    ncRNA = auto()
    lncRNA = auto()

@dataclass
class RNAProperties:
    type: RNAType

class RNAEmbedding:
    def __init__(self, rna_type: RNAType, embedding_dim: int = 64):
        self.rna_type = rna_type
        self.embedding_dim = embedding_dim

    def encode_sequence(self, sequence: str) -> np.ndarray:
        # Dummy implementation
        return np.eye(self.embedding_dim)

    def pool_to_single(self, encoded: np.ndarray) -> np.ndarray:
        # Dummy implementation
        return np.eye(self.embedding_dim) / self.embedding_dim
