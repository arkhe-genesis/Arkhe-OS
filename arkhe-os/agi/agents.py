# =========================================================
# Agentes AGI - Inteligencia Canonica Distribuida
# Substrato 229/378/392
# =========================================================
import random, math, time, hashlib, json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AGIAgent:
    id: str
    region: str
    expertise: str
    framework: str
    phi_c_regional: float = 0.95
    events_processed: int = 0

    def classify_event(self, event: dict) -> dict:
        """Classifica um evento de particula com base na expertise."""
        amp = event.get("amplitude_mV", event.get("amplitude", 0))
        integ = event.get("integral_nVs", event.get("integral", 0))
        width = event.get("width_ns", 10)
        ratio = integ / amp if amp > 0 else 0

        if self.expertise == "muon":
            if amp > 600 and ratio > 5:
                return {"class": "MUON", "confidence": 0.92, "energy_mev": amp * 0.1}
        elif self.expertise == "electron":
            if 300 < amp < 700 and 3 < ratio < 7:
                return {"class": "ELECTRON", "confidence": 0.88, "energy_mev": amp * 0.05}
        elif self.expertise == "photon":
            if amp < 400 and ratio < 4:
                return {"class": "PHOTON", "confidence": 0.85, "energy_mev": amp * 0.02}
        elif self.expertise == "neutron":
            if amp < 100:
                return {"class": "NEUTRON", "confidence": 0.75, "energy_mev": 0}
        elif self.expertise == "calorimetry":
            energy = integ * 0.01
            return {"class": "ANY", "confidence": 0.80, "energy_mev": energy}
        elif self.expertise == "trigger":
            if amp > 500:
                return {"class": "TRIGGER", "confidence": 0.95, "action": "SEND_TO_PRIMAKOFF"}
        return {"class": "UNKNOWN", "confidence": 0.3, "energy_mev": 0}

    def deliberate(self, sensor_data: dict) -> dict:
        """Simula deliberacao AGI para tomada de decisao."""
        mag = sensor_data.get("seismic", {}).get("mag", 0)
        if mag > 7.5:
            decision = "COMMIT_ALERT"
            confidence = 0.98
        else:
            decision = "ABSTAIN"
            confidence = 0.7
        return {
            "agent_id": self.id,
            "vote": decision,
            "confidence": confidence,
            "explanation": f"Agent {self.id} ({self.expertise}) using {self.framework}"
        }

class AGIConsensus:
    """Consenso AGI-Ghost para decisoes coletivas."""

    def __init__(self, agents: List[AGIAgent]):
        self.agents = agents

    def classify_event(self, event: dict) -> dict:
        if not self.agents:
            return {"class": "UNKNOWN", "votes": 0, "total_agents": 0, "avg_confidence": 0.0, "quorum_reached": False}

        votes = []
        for agent in self.agents:
            result = agent.classify_event(event)
            votes.append(result)

        classes = {}
        for v in votes:
            cls = v["class"]
            if cls not in classes:
                classes[cls] = {"count": 0, "confidence_sum": 0}
            classes[cls]["count"] += 1
            classes[cls]["confidence_sum"] += v["confidence"]

        winner = max(classes.items(), key=lambda x: x[1]["count"])
        return {
            "class": winner[0],
            "votes": winner[1]["count"],
            "total_agents": len(self.agents),
            "avg_confidence": winner[1]["confidence_sum"] / winner[1]["count"],
            "quorum_reached": winner[1]["count"] >= len(self.agents) * 2/3
        }

    def deliberate_alert(self, sensor_data: dict) -> dict:
        decisions = [agent.deliberate(sensor_data) for agent in self.agents]
        yes_votes = sum(1 for d in decisions if d["vote"] == "COMMIT_ALERT")
        quorum = len(self.agents) * 2/3
        return {
            "consensus_reached": yes_votes >= quorum,
            "yes_votes": yes_votes,
            "total_agents": len(self.agents),
            "quorum": quorum,
            "decisions": decisions
        }
