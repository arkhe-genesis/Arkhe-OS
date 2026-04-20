from rdflib import Graph, Namespace, URIRef, RDF
from typing import List, Dict

class OntologyClient:
    """
    Cliente local/remoto para a ontologia Arkhe.
    Simula consulta ao Fuseki usando rdflib para portabilidade em testes.
    """
    def __init__(self, ontology_path: str = "src/arkhe_core/ontology/arkhe_ontology.owl"):
        self.g = Graph()
        try:
            self.g.parse(ontology_path, format="xml")
        except:
            pass
        self.ns = Namespace("http://arkhe.ai/ontology/2026#")

    def validate_agent_task(self, agent_id: str, task_type: str) -> bool:
        """
        Consulta a ontologia local: este agente pode executar este tipo de tarefa?
        """
        query = f"""
        PREFIX arkhe: <http://arkhe.ai/ontology/2026#>
        ASK {{
            arkhe:{agent_id} rdf:type arkhe:Agent .
            arkhe:{task_type} rdf:type arkhe:Task .
        }}
        """
        # Mocking logic for validation if graph is empty
        if len(self.g) == 0:
             return True
        results = self.g.query(query)
        return bool(results)

    def get_required_seals(self, task_id: str) -> List[str]:
        query = f"""
        PREFIX arkhe: <http://arkhe.ai/ontology/2026#>
        SELECT ?seal WHERE {{
            arkhe:{task_id} arkhe:protectedBy ?seal .
        }}
        """
        if len(self.g) == 0:
             return ["TEMPORAL"]
        results = self.g.query(query)
        return [str(row[0]).split('#')[-1] for row in results]
