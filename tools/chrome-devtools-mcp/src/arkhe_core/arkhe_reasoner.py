"""
arkhe_reasoner.py
Motor de inferência OWL RL para a Ontologia Arkhe.
Implementa forward chaining sobre RDFlib com regras de produção.
"""

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from typing import Set, Tuple, Callable, Dict, List
import time
import os

ARKHE = Namespace("http://arkhe.ai/ontology/2026#")

class ArkheReasoner:
    """
    Motor de inferência OWL RL. Aplica regras de produção até ponto fixo.
    Equivalente ao functor de navegação no grafo de conhecimento.
    """

    def __init__(self, ontology_path: str = "src/arkhe_core/ontology/arkhe_ontology.owl"):
        self.g = Graph()
        if os.path.exists(ontology_path):
            self.g.parse(ontology_path, format="xml")
        self.g.bind("arkhe", ARKHE)

        # Registro de regras OWL RL
        self.rules: List[Callable[[], int]] = [
            self._rule_subclass_transitivity,
            self._rule_swrl_drift_compromise,
        ]

        self.inferred = 0
        self.iterations = 0

    def _triples(self, s=None, p=None, o=None):
        return list(self.g.triples((s, p, o)))

    def _add(self, s, p, o):
        if (s, p, o) not in self.g:
            self.g.add((s, p, o))
            self.inferred += 1
            return True
        return False

    def _rule_subclass_transitivity(self) -> int:
        count = 0
        for a, _, b in self._triples(None, RDFS.subClassOf, None):
            for _, _, d in self._triples(b, RDFS.subClassOf, None):
                if self._add(a, RDFS.subClassOf, d):
                    count += 1
        return count

    def _rule_swrl_drift_compromise(self) -> int:
        count = 0
        compromised = ARKHE.CompromisedAgent

        for agent in self.g.subjects(RDF.type, ARKHE.Agent):
            states = list(self.g.objects(agent, ARKHE.hasState))
            seals = list(self.g.objects(agent, ARKHE.protectedBy))

            has_drift = any(
                (s, RDF.type, ARKHE.DriftState) in self.g
                for s in states
            )
            has_semantic = any(
                (s, RDF.type, ARKHE.SemanticSeal) in self.g
                for s in seals
            )

            if has_drift and not has_semantic:
                if self._add(agent, RDF.type, compromised):
                    count += 1
        return count

    def materialize(self, max_iterations: int = 10) -> Dict:
        start_time = time.time()
        total_inferred = 0

        for i in range(max_iterations):
            self.iterations = i + 1
            iteration_inferred = 0
            for rule in self.rules:
                iteration_inferred += rule()
            if iteration_inferred == 0:
                break
            total_inferred += iteration_inferred

        return {
            "iterations": self.iterations,
            "triples_inferred": total_inferred,
            "total_triples": len(self.g),
            "time_ms": (time.time() - start_time) * 1000
        }

    def query(self, sparql: str):
        return list(self.g.query(sparql))

if __name__ == "__main__":
    reasoner = ArkheReasoner()
    result = reasoner.materialize()
    print(f"Materialização concluída: {result}")

    q = """
    PREFIX arkhe: <http://arkhe.ai/ontology/2026#>
    SELECT ?agent WHERE {
        ?agent rdf:type arkhe:CompromisedAgent .
    }
    """
    compromised = reasoner.query(q)
    print(f"Agentes comprometidos: {len(compromised)}")
    for row in compromised:
        print(f"  - {row[0]}")
