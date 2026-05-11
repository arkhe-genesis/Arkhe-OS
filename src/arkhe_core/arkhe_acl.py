"""
arkhe_acl.py
Anti-Corruption Layer entre AgentContext e ResourceContext.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime, timezone

from typing import Callable, Any

@dataclass
class ACLForall:
    collection: List[Any]
    predicate: Callable[[Any], bool]

    def evaluate(self) -> bool:
        return all(self.predicate(item) for item in self.collection)

@dataclass
class ACLExists:
    collection: List[Any]
    predicate: Callable[[Any], bool]

    def evaluate(self) -> bool:
        return any(self.predicate(item) for item in self.collection)

@dataclass
class AgentTaskAssigned:
    task_id: str
    agent_id: str
    task_type: str
    complexity_score: float
    required_tokens: int
    quantum_preference: bool
    timestamp: datetime
    metadata: Dict[str, Any] = None  # Support for rich data types
    tags: List[str] = None           # Support for rich data types

@dataclass
class ResourceAllocationRequest:
    job_id: str
    compute_profile: str
    memory_mb: int
    estimated_duration_ms: int
    priority: int
    verified_contract: bool = False

class AgentToResourceACL:
    def validate_contract(self, event: AgentTaskAssigned) -> bool:
        """
        Garante que os contratos são verificáveis usando quantificadores expressivos.
        """
        if event.tags is None:
            return True

        # Exemplo de regra ACL usando Forall: Todas as tags devem ser minúsculas
        all_tags_valid = ACLForall(event.tags, lambda t: t.islower()).evaluate()

        # Exemplo de regra ACL usando Exists: Deve existir uma tag de segurança se a complexidade for alta
        if event.complexity_score > 0.8:
            has_security_tag = ACLExists(event.tags, lambda t: "security" in t).evaluate()
            return all_tags_valid and has_security_tag

        return all_tags_valid

    def translate(self, event: AgentTaskAssigned) -> ResourceAllocationRequest:
        is_contract_valid = self.validate_contract(event)
        if not is_contract_valid:
            raise ValueError("ACL Contract Validation Failed.")

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
            priority=priority,
            verified_contract=True
        )

if __name__ == "__main__":
    acl = AgentToResourceACL()
    event = AgentTaskAssigned(
        task_id="task-1",
        agent_id="agent-1",
        task_type="QEC",
        complexity_score=0.95,
        required_tokens=8192,
        quantum_preference=True,
        timestamp=datetime.now(),
        tags=["quantum", "security"]
    )
    request = acl.translate(event)
    print(f"ACL Trans: {event.task_type} -> {request.compute_profile} (mem={request.memory_mb}MB)")
