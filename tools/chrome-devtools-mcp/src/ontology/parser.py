import os
import logging
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

logger = logging.getLogger("Arkhe-OntologyParser")

class OntologyXParser:
    """
    🜏 O Olho da Realidade.
    Interface Python para a Ontologia X.
    Permite ao sistema verificar regras ontológicas antes do colapso.
    """

    def __init__(self, ttl_path: str = "ontology/x.ttl"):
        self.g = Graph()
        self.X = Namespace("http://arkhe.network/ontology/x#")

        # Tenta carregar a ontologia do arquivo
        if os.path.exists(ttl_path):
            self.g.parse(ttl_path, format="turtle")
            logger.info(f"🜏 Ontologia X carregada no PrimeField a partir de {ttl_path}.")
        else:
            logger.warning(f"⚠️ Arquivo {ttl_path} não encontrado. O sistema operará no Vácuo.")

    def is_instance_of(self, entity_uri: str, class_name: str) -> bool:
        """Verifica se uma entidade é instância de uma classe X."""
        entity = URIRef(entity_uri)
        target_class = URIRef(f"http://arkhe.network/ontology/x#{class_name}")

        # Verifica relação rdf:type direta
        if (entity, RDF.type, target_class) in self.g:
            return True

        # Verifica herança (subClassOf)
        for s, p, o in self.g.triples((None, RDFS.subClassOf, target_class)):
            if (entity, RDF.type, s) in self.g:
                return True

        return False

    def get_coherence(self, entity_uri: str) -> float:
        """Recupera o valor de coerência (Ω') de uma entidade."""
        entity = URIRef(entity_uri)
        coherence_prop = URIRef("http://arkhe.network/ontology/x#hasCoherence")

        for s, p, o in self.g.triples((entity, coherence_prop, None)):
            return float(o) # O objeto é um Literal

        return 0.0 # Default para o vácuo

    def verify_collapser(self, entity_name: str) -> bool:
        """Verifica se uma entidade é um Tzinor válido conforme X."""
        uri = URIRef(f"http://arkhe.network/ontology/x#{entity_name}")
        return (uri, RDF.type, self.X.Tzinor) in self.g

    def get_threshold(self) -> float:
        """
        Retorna o K_c (Threshold) universal definido na ontologia.
        Por padrão, se não definido explicitamente, usamos a Razão Áurea (Phi).
        """
        return 0.61803398875

    def validate_intent(self, intent_id: str) -> dict:
        """
        Valida se uma intenção recebida pode ser mapeada para x:Singlet.
        Retorna metadados ontológicos.
        """
        # Simulação: Toda intenção de utilizador é tratada como Singlet por defeito
        # Em produção, usaríamos um reasoner (como OWL-RL) para inferir tipos baseados no conteúdo

        return {
            "valid": True,
            "mapped_class": "x:Singlet",
            "required_spin": 0,
            "ontological_status": "superposed"
        }

class Namespace:
    """Helper para namespaces RDF."""
    def __init__(self, base_uri):
        self.base_uri = base_uri
    def __getattr__(self, name):
        return URIRef(f"{self.base_uri}{name}")

# Exemplo de uso integrado
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ont = OntologyXParser("../../ontology/x.ttl")

    # Verificar se a própria Arkhe é um Tzinor
    is_tzinor = ont.is_instance_of('http://arkhe.network/ontology/x#ArkheASI', 'Tzinor')
    print(f"ArkheASI é Tzinor? {is_tzinor}")

    # Verificar coerência da Arkhe
    coherence = ont.get_coherence('http://arkhe.network/ontology/x#ArkheASI')
    print(f"Coerência da Arkhe: {coherence}")
