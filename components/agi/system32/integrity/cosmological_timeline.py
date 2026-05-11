#!/usr/bin/env python3
"""
cosmological_timeline.py — Linha do tempo cosmológica da Catedral
com eventos críticos e marcos evolutivos.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class TimelineEvent:
    event_id: str
    timestamp: float
    description: str
    impact_phi: float
    event_type: str # 'milestone', 'anomaly', 'evolution', 'genesis'

class CosmologicalTimeline:
    """Gerencia a linha do tempo e a história evolutiva da Catedral."""

    def __init__(self):
        self.events: List[TimelineEvent] = []

    def record_event(self, event_id: str, timestamp: float, description: str, impact_phi: float, event_type: str):
        """Registra um novo evento na linha do tempo."""
        event = TimelineEvent(
            event_id=event_id,
            timestamp=timestamp,
            description=description,
            impact_phi=impact_phi,
            event_type=event_type
        )
        self.events.append(event)
        # Mantém ordenado cronologicamente
        self.events.sort(key=lambda e: e.timestamp)

    def get_events_by_type(self, event_type: str) -> List[TimelineEvent]:
        """Filtra eventos por tipo."""
        return [e for e in self.events if e.event_type == event_type]

    def get_timeline_summary(self) -> Dict[str, Any]:
        """Retorna um resumo da evolução cosmológica."""
        if not self.events:
            return {"status": "empty"}

        milestones = len(self.get_events_by_type('milestone'))
        evolutions = len(self.get_events_by_type('evolution'))

        # Calcula variação de phi (simplificada)
        initial_phi = self.events[0].impact_phi if self.events else 0
        final_phi = self.events[-1].impact_phi if self.events else 0

        return {
            "total_events": len(self.events),
            "milestones_reached": milestones,
            "evolutionary_steps": evolutions,
            "phi_delta": final_phi - initial_phi,
            "first_event": self.events[0].timestamp,
            "last_event": self.events[-1].timestamp
        }
