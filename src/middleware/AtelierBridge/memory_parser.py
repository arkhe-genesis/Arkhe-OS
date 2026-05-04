# src/middleware/AtelierBridge/memory_parser.py
"""
Memory Parser — Extracts collapsed events from MEMORY.md
Arkhe-Block: 847.812 | Synapse-κ
"""

import re
from typing import List
from dataclasses import dataclass
from datetime import datetime, timezone
from .cst_parser import CognitiveNode

@dataclass
class MemoryEvent:
    timestamp: float
    event_type: str
    description: str
    emotional_valence: float
    linked_dream: str

class MemoryParser:
    """Parser para MEMORY.md — formato: ## [timestamp] Evento"""

    EVENT_PATTERN = re.compile(
        r"##\s*\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]\s*(.+?)\n"
        r"(.*?)(?=\n##|\Z)",
        re.DOTALL
    )

    def __init__(self, memory_content: str):
        self.content = memory_content
        self.events: List[MemoryEvent] = []

    def parse(self) -> List[CognitiveNode]:
        matches = self.EVENT_PATTERN.finditer(self.content)
        nodes = []

        for match in matches:
            ts_str, event_type, description = match.groups()
            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

            valence_match = re.search(r"valência[:\s]*([-+]?[\d.]+)", description)
            emotional_valence = float(valence_match.group(1)) if valence_match else 0.0

            dream_match = re.search(r"sonho[:\s]*\[([^\]]+)\]", description)
            linked_dream = dream_match.group(1) if dream_match else ""

            node = CognitiveNode(
                node_type="memory",
                content=description.strip(),
                confidence=1.0,
                dependencies=[linked_dream] if linked_dream else [],
                phase_signature=complex(0, 0)
            )
            nodes.append(node)
        return nodes
