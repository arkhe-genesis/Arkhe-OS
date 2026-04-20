"""
arkhe_integration.py
Integração entre o Motor de Inferência (Ontologia) e o Orquestrador (LangGraph).
"""

from .arkhe_reasoner import ArkheReasoner
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ExecutionPlan:
    agent_id: str
    tasks: List[Dict]
    required_seals: List[str]
    fallback_strategy: str
    estimated_risk: float

class OntologyDrivenOrchestrator:
    def __init__(self, ontology_path: str = "src/arkhe_core/ontology/arkhe_ontology.owl"):
        self.reasoner = ArkheReasoner(ontology_path)
        self.reasoner.materialize()

    def plan_workflow(self, agent_uri: str, task_uri: str) -> ExecutionPlan:
        # Query: Quais seals protegem o agente?
        q_seals = f"""
        PREFIX arkhe: <http://arkhe.ai/ontology/2026#>
        SELECT ?seal ?type WHERE {{
            <{agent_uri}> arkhe:protectedBy ?seal .
            ?seal rdf:type ?type .
        }}
        """
        seals = [str(row[0]).split("#")[-1] for row in self.reasoner.query(q_seals)]

        # Query: O agente está comprometido?
        q_compromised = f"""
        PREFIX arkhe: <http://arkhe.ai/ontology/2026#>
        ASK {{
            <{agent_uri}> rdf:type arkhe:CompromisedAgent .
        }}
        """
        is_compromised = bool(self.reasoner.query(q_compromised))

        risk = 0.9 if is_compromised else 0.1
        fallback = "ABORT" if is_compromised else "DEGRADE"

        return ExecutionPlan(
            agent_id=agent_uri.split("#")[-1],
            tasks=[{"task": task_uri.split("#")[-1]}],
            required_seals=seals,
            fallback_strategy=fallback,
            estimated_risk=risk
        )
