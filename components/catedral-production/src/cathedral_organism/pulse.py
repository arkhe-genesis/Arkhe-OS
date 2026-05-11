# catedral-production/src/cathedral_organism/pulse.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class OrganismPulse:
    region_id: str
    timestamp: float
    local_omega: float
    global_omega: float
    subsystem_health: Dict[str, float]
    cross_region_latency_ms: float
    shard_count: int
    pending_tasks: int

@dataclass
class NodeHealthPulse:
    region_id: str
    omega: float
    load: float
