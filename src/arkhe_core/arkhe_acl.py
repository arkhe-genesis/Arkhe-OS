"""
arkhe_acl.py
Anti-Corruption Layer entre AgentContext e ResourceContext.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime, timezone

@dataclass
class AgentTaskAssigned:
    task_id: str
    agent_id: str
    task_type: str
    complexity_score: float
    required_tokens: int
    quantum_preference: bool
    timestamp: datetime

@dataclass
class ResourceAllocationRequest:
    job_id: str
    compute_profile: str
    memory_mb: int
    estimated_duration_ms: int
    priority: int

class AgentToResourceACL:
    def translate(self, event: AgentTaskAssigned) -> ResourceAllocationRequest:
        # Functor de tradução: preserva invariantes, descarta semântica irrelevante.
        profile = "SMALL_GPU"
        if event.quantum_preference and event.complexity_score > 0.8:
            profile = "QUANTUM_AOD"
        elif event.complexity_score > 0.8:
            profile = "LARGE_GPU"
        elif event.complexity_score > 0.4:
            profile = "MEDIUM_GPU"

        memory_mb = int(event.required_tokens * 0.5) + 4096
        priority = 5

        return ResourceAllocationRequest(
            job_id=event.task_id,
            compute_profile=profile,
            memory_mb=memory_mb,
            estimated_duration_ms=500,
            priority=priority
        )

if __name__ == "__main__":
    acl = AgentToResourceACL()
    event = AgentTaskAssigned("task-1", "agent-1", "QEC", 0.95, 8192, True, datetime.now())
    request = acl.translate(event)
    print(f"ACL Trans: {event.task_type} -> {request.compute_profile} (mem={request.memory_mb}MB)")
