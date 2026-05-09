# src/middleware/AtelierBridge/cst_parser.py
"""
Cognitive Syntax Tree (CST) Parser
Arkhe-Block: 847.807 | Synapse-κ

Extrai estruturas semânticas do Markdown via gramática de atribuição sintática.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import re
import hashlib
import numpy as np

@dataclass
class CognitiveNode:
    node_type: str          # 'metaphor', 'invariant', 'projection', 'memory'
    content: str            # Texto original
    confidence: float       # [0,1] — certeza da classificação
    dependencies: List[str]  # IDs de nós referenciados
    phase_signature: complex # Amplitude no espaço de fase C

    def to_lean(self) -> str:
        """Gera representação Lean 4 do nó"""
        if self.node_type == "invariant":
            return f"def {self.lean_id} : Prop := {self.content}"
        elif self.node_type == "metaphor":
            return f"structure {self.lean_id} where\n  source : Type\n  target : Type\n  mapping : source → target"
        return f"-- node {self.lean_id} of type {self.node_type}"

    @property
    def lean_id(self) -> str:
        """Identificador único para Lean"""
        return f"cog_{hashlib.sha256(self.content.encode()).hexdigest()[:8]}"

class SoulParser:
    """Parser específico para SOUL.md — extrai invariantes de identidade"""

    INVARIANT_PATTERNS = [
        r"(?i)eu sou[:\s]+(.+?)(?:\.|$)",           # "Eu sou..."
        r"(?i)nunca mud[oa][:\s]+(.+?)(?:\.|$)",     # "Nunca mudo..."
        r"(?i)essência[:\s]+(.+?)(?:\.|$)",          # "Essência: ..."
        r"(?i)valor.*fundamental[:\s]+(.+?)(?:\.|$)" # "Valores fundamentais"
    ]

    def __init__(self, soul_content: str):
        self.content = soul_content
        self.nodes: List[CognitiveNode] = []
        self.entropy = 0.0

    def parse(self) -> List[CognitiveNode]:
        """Extrai invariantes como nós cognitivos"""
        for pattern in self.INVARIANT_PATTERNS:
            matches = re.finditer(pattern, self.content, re.MULTILINE)
            for match in matches:
                invariant_text = match.group(1).strip()
                node = CognitiveNode(
                    node_type="invariant",
                    content=invariant_text,
                    confidence=0.85,
                    dependencies=[],
                    phase_signature=complex(
                        self._compute_phase_real(invariant_text),
                        self._compute_phase_imag(invariant_text)
                    )
                )
                self.nodes.append(node)

        self.entropy = self._compute_entropy()
        return self.nodes

    def _compute_phase_real(self, text: str) -> float:
        h = hashlib.sha256(text.encode()).digest()
        return int.from_bytes(h[:4], 'big') / (2**32)

    def _compute_phase_imag(self, text: str) -> float:
        h = hashlib.sha256(text.encode()).digest()
        return int.from_bytes(h[4:8], 'big') / (2**32)

    def _compute_entropy(self) -> float:
        from collections import Counter
        type_counts = Counter(n.node_type for n in self.nodes)
        total = len(self.nodes) or 1
        probs = [c/total for c in type_counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
