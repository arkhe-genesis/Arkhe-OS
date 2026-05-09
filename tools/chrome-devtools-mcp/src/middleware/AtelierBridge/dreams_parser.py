# src/middleware/AtelierBridge/dreams_parser.py
"""
Dreams Parser — Extracts future projections from DREAMS.md
Arkhe-Block: 847.812 | Synapse-κ
"""

import re
from typing import List
from dataclasses import dataclass
from .cst_parser import CognitiveNode

@dataclass
class DreamProjection:
    dream_id: str
    title: str
    description: str
    probability: float
    coherence_requirement: float
    linked_memory: str

class DreamsParser:
    """Parser para DREAMS.md — formato: ## [ID] Sonho"""

    DREAM_PATTERN = re.compile(
        r"##\s*\[([^\]]+)\]\s*(.+?)\n"
        r"(.*?)(?=\n##|\Z)",
        re.DOTALL
    )

    def __init__(self, dreams_content: str):
        self.content = dreams_content

    def parse(self) -> List[CognitiveNode]:
        matches = self.DREAM_PATTERN.finditer(self.content)
        nodes = []

        for match in matches:
            dream_id, title, description = match.groups()

            prob_match = re.search(r"probabilidade[:\s]*([\d.]+)", description)
            prob = float(prob_match.group(1)) if prob_match else 0.5

            lambda_match = re.search(r"λ₂\s*m[ií]nima?[:\s]*([\d.]+)", description)
            lambda_req = float(lambda_match.group(1)) if lambda_match else 0.85

            memory_match = re.search(r"memória[:\s]*\[([^\]]+)\]", description)
            linked_mem = memory_match.group(1) if memory_match else ""

            node = CognitiveNode(
                node_type="projection",
                content=description.strip(),
                confidence=prob,
                dependencies=[linked_mem] if linked_mem else [],
                phase_signature=complex(0.618, 0.382)
            )
            nodes.append(node)
        return nodes
