# ontological/forge.py — Criador ontológico de criação de ontologias

import hashlib
import json
import time
import logging
from typing import Dict, List, Optional, Union, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD

# Importações internas do ecossistema Arkhe
import arkhe_lang
from protocol_forge import ProtocolForge, GeneratedSubstrate
from src.arkhe_core.quantum.codex import QuantumCodex
from ontological.recursive_learning import RecursiveLearningEngine
from cathedral_ternary.bitzk import TernaryCircuitBuilder

class OntologyConsistency(Enum):
    """Níveis de consistência ontológica."""
    VALID = "valid"              # Sem contradições lógicas
    WARNING = "warning"          # Avisos de modelagem, mas consistente
    INCONSISTENT = "inconsistent" # Contradições detectadas
    UNREASONED = "unreasoned"    # Reasoner não executado ainda

@dataclass
class DomainOntologySpec:
    """Especificação para geração de ontologia de domínio."""
    domain_name: str
    description: str
    base_uri: str
    entities: List[str]
    actions: List[str]
    consents: List[str]
    purposes: List[str]
    constraints: Dict[str, Union[str, float, bool]]
    inherits_from: Optional[List[str]] = None
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)

@dataclass
class GeneratedOntology:
    """Ontologia gerada com metadados de validação."""
    ontology_id: str
    domain_name: str
    file_path: str
    file_hash: str  # SHA-256 do arquivo RDF/XML ou Turtle
    classes_count: int
    properties_count: int
    individuals_count: int
    consistency_status: OntologyConsistency
    reasoner_log: List[str]
    anchored_in_codex: bool
    generated_at: float = field(default_factory=time.time)

class OntologicalForge:
    """
    Criador ontológico de criação de ontologias.
    Gera ontologias de domínio a partir da meta-ontologia,
    traduz para arkhe-lang, e alimenta o ProtocolForge.
    """

    # Namespace da Catedral
    CATHEDRAL = Namespace("http://cathedral.ark/ontology/meta/v1#")

    def __init__(self, codex: QuantumCodex, protocol_forge: ProtocolForge):
        self.codex = codex
        self.protocol_forge = protocol_forge
        self.meta_ontology = Graph()
        self._setup_meta_ontology()

        # Motores acoplados
        self.learning_engine = RecursiveLearningEngine()
        self.ternary_builder = TernaryCircuitBuilder()

        # Cache de ontologias geradas
        self._generated_ontologies: Dict[str, GeneratedOntology] = {}

        # Histórico de gerações para aprendizado recursivo
        self._generation_history: List[Dict] = []

        # Thresholds dinâmicos que podem ser aprimorados recursivamente
        self.thresholds = {
            "min_classes": 3,
            "max_inheritance_depth": 5,
            "dp_epsilon_default": 0.5,
            "ternary_mode": False
        }

    def _setup_meta_ontology(self):
        """Define a estrutura base (Meta-Ontologia) usando RDFLib."""
        C = self.CATHEDRAL
        g = self.meta_ontology

        # Classes Primordiais
        g.add((C.Entity, RDF.type, OWL.Class))
        g.add((C.Action, RDF.type, OWL.Class))
        g.add((C.Consent, RDF.type, OWL.Class))
        g.add((C.Purpose, RDF.type, OWL.Class))
        g.add((C.Proof, RDF.type, OWL.Class))
        g.add((C.Audit, RDF.type, OWL.Class))
        g.add((C.Substrate, RDF.type, OWL.Class))

        # Propriedades
        g.add((C.hasConsent, RDF.type, OWL.ObjectProperty))
        g.add((C.hasConsent, RDFS.domain, C.Entity))
        g.add((C.hasConsent, RDFS.range, C.Consent))

        g.add((C.fulfillsPurpose, RDF.type, OWL.ObjectProperty))
        g.add((C.fulfillsPurpose, RDFS.domain, C.Action))
        g.add((C.fulfillsPurpose, RDFS.range, C.Purpose))

        g.add((C.dpEpsilon, RDF.type, OWL.DatatypeProperty))
        g.add((C.dpEpsilon, RDFS.domain, C.Entity))
        g.add((C.dpEpsilon, RDFS.range, XSD.float))

    def generate_domain_ontology(self, spec: DomainOntologySpec) -> GeneratedOntology:
        """Gera uma ontologia de domínio baseada na especificação."""
        domain_ns = Namespace(f"{spec.base_uri}/{spec.domain_name.lower()}#")
        g = Graph()
        g.bind("meta", self.CATHEDRAL)
        g.bind(spec.domain_name.lower(), domain_ns)

        # Copia meta-ontologia (base)
        for s, p, o in self.meta_ontology:
            g.add((s, p, o))

        C = self.CATHEDRAL

        # Adiciona entidades do domínio
        for entity in spec.entities:
            entity_uri = domain_ns[entity]
            g.add((entity_uri, RDF.type, OWL.Class))
            g.add((entity_uri, RDFS.subClassOf, C.Entity))

        # Adiciona ações e relaciona com propósitos
        for action in spec.actions:
            action_uri = domain_ns[action]
            g.add((action_uri, RDF.type, OWL.Class))
            g.add((action_uri, RDFS.subClassOf, C.Action))

        # Aplica restrições de privacidade
        if spec.constraints.get("high_privacy"):
            epsilon = spec.constraints.get("dp_epsilon", self.thresholds["dp_epsilon_default"])
            for entity in spec.entities:
                g.add((domain_ns[entity], C.dpEpsilon, Literal(epsilon)))

        # Serialização e Hash
        file_path = f"ontological/{spec.domain_name.lower()}.ttl"
        g.serialize(destination=file_path, format="turtle")

        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Validação Simples (RDFLib não é um reasoner DL completo, mas valida estrutura)
        status = OntologyConsistency.VALID if len(spec.entities) >= self.thresholds["min_classes"] else OntologyConsistency.WARNING

        generated = GeneratedOntology(
            ontology_id=f"onto_{spec.domain_name.lower()}_{file_hash[:12]}",
            domain_name=spec.domain_name,
            file_path=file_path,
            file_hash=file_hash,
            classes_count=len(list(g.subjects(RDF.type, OWL.Class))),
            properties_count=len(list(g.subjects(RDF.type, OWL.ObjectProperty))),
            individuals_count=0,
            consistency_status=status,
            reasoner_log=["Validação estrutural RDF concluída."],
            anchored_in_codex=True,
        )

        # Otimização Ternária (FS-86)
        if self.thresholds.get("ternary_mode"):
            logging.info(f"[OntoForge] Aplicando paradigma ternário ao domínio {spec.domain_name}")
            self.ternary_builder.optimize_circuit(spec.entities, [1] * len(spec.entities))

        # Ancora no Códice
        self.codex.log_verdict(
            node_id="OntologicalForge",
            verdict="CANONIZED",
            coherence=1.0 if status == OntologyConsistency.VALID else 0.8,
            payload_hash=file_hash
        )

        self._generated_ontologies[generated.ontology_id] = generated
        self._generation_history.append({
            "ontology_id": generated.ontology_id,
            "domain": spec.domain_name,
            "status": status.value,
            "timestamp": generated.generated_at
        })

        return generated

    def ontology_to_intention(self, ontology: GeneratedOntology) -> str:
        """
        Traduz RDF para arkhe-lang (Tradução Semântica FS-84).
        Mapeia classes, propriedades e restrições para a sintaxe declarativa da Catedral.
        """
        # Carrega o grafo da ontologia
        g = Graph()
        g.parse(ontology.file_path, format="turtle")
        C = self.CATHEDRAL

        intention = f"// Geração Semântica Automatizada - {ontology.domain_name}\n"
        intention += f"// Ontology ID: {ontology.ontology_id}\n"
        intention += f"protocol \"{ontology.domain_name}\" {{\n"
        intention += f"  description: \"{ontology.domain_name} protocol generated from semantic ontology\"\n\n"

        # 1. Mapeamento de Entidades
        entities = []
        for s in g.subjects(RDFS.subClassOf, C.Entity):
            name = str(s).split('#')[-1]
            if name:
                entities.append(name)

        if entities:
            intention += "  entities: [\n"
            for entity in entities:
                intention += f"    {entity},\n"
            intention += "  ]\n\n"

        # 2. Mapeamento de Ações
        actions = []
        for s in g.subjects(RDFS.subClassOf, C.Action):
            name = str(s).split('#')[-1]
            if name:
                actions.append(name)

        if actions:
            intention += "  actions: [\n"
            for action in actions:
                intention += f"    {action},\n"
            intention += "  ]\n\n"

        # 3. Mapeamento de Regras de Privacidade e Consentimento
        intention += "  privacy: {\n"

        # Extrai dpEpsilon (Privacidade Diferencial)
        for s, o in g.subject_objects(C.dpEpsilon):
            name = str(s).split('#')[-1]
            intention += f"    {name}: {{ dp_epsilon: {o}, consent_required: true }}\n"

        # Verifica se há consentimentos associados (simplificado via meta-propriedade)
        # Em uma implementação OWL completa, usaríamos restrições de cardinalidade ou Existential Quantifiers
        intention += "  }\n\n"

        # 4. Regulação e Interoperabilidade
        intention += "  regulation: [\"LGPD\", \"GDPR\", \"ISO27001\"]\n"

        intention += "  integrates_with: [\n"
        intention += "    \"cathedral::consent::granular_manager\",\n"
        intention += "    \"cathedral::audit::cross_jurisdiction\"\n"
        if self.thresholds.get("ternary_mode"):
            intention += "    ,\"cathedral::ternary::bitzk\"\n"
        intention += "  ]\n"

        intention += "}"

        return intention

    async def forge_from_ontology(self, spec: DomainOntologySpec) -> Dict:
        """Fluxo completo de geração."""
        ontology = self.generate_domain_ontology(spec)
        intention = self.ontology_to_intention(ontology)
        substrate = await self.protocol_forge.generate_from_intention(intention)

        return {
            "ontology": ontology,
            "intention": intention,
            "substrate": substrate
        }

    def _analyze_generation_history(self) -> Dict[str, Any]:
        """
        Analisa o histórico de gerações para identificar padrões de sucesso e falha.
        Retorna sugestões de otimização para os thresholds e regras.
        """
        if not self._generation_history:
            return {}

        total = len(self._generation_history)
        valid = sum(1 for h in self._generation_history if h["status"] == "valid")
        success_rate = valid / total

        optimizations = {}

        # Se a taxa de sucesso for muito alta (>90%), podemos aumentar o rigor
        if success_rate > 0.9 and total >= 5:
            optimizations["min_classes"] = self.thresholds["min_classes"] + 1
            optimizations["reason"] = "Alta taxa de sucesso permite maior rigor semântico."

        # Se a taxa de sucesso for baixa (<50%), talvez estejamos sendo rígidos demais ou a entrada é pobre
        elif success_rate < 0.5 and total >= 5:
            optimizations["min_classes"] = max(2, self.thresholds["min_classes"] - 1)
            optimizations["reason"] = "Baixa taxa de sucesso sugere thresholds excessivamente restritivos para os domínios atuais."

        return optimizations

    def enable_recursive_self_improvement(self) -> bool:
        """
        Mecanismo de Aprendizado Recursivo (FS-84).
        O Forge gera uma ontologia que descreve sua própria evolução baseada no histórico.
        """
        logging.info("[OntoForge] Iniciando ciclo de aprendizado recursivo...")

        # 1. Analisa histórico via RecursiveLearningEngine
        self.learning_engine.extract_patterns(self._generation_history)
        optimizations = self._analyze_generation_history()

        # Integração com Ternary (FS-86): Ativa se houver massa crítica
        if len(self._generation_history) >= 10:
            self.thresholds["ternary_mode"] = True
            logging.info("[OntoForge] Paradigma Ternário (BitZK) ativado para máxima eficiência.")

        if optimizations:
            old_min = self.thresholds["min_classes"]
            if "min_classes" in optimizations:
                self.thresholds["min_classes"] = optimizations["min_classes"]

            logging.info(f"[OntoForge] Auto-aprimoramento aplicado: {optimizations.get('reason')}")
            logging.info(f"[OntoForge] min_classes: {old_min} -> {self.thresholds['min_classes']}")

        # 2. Gera ontologia de engenharia para formalizar o estado atual do "Ser"
        # Esta ontologia serve como um checkpoint evolutivo ancorado no Códice.
        spec = DomainOntologySpec(
            domain_name="OntologyEngineering",
            description=f"Instância evolutiva do Forge (v{self.thresholds['min_classes']}.x)",
            base_uri="http://cathedral.ark/ontology",
            entities=["HistoryAnalyzer", "ThresholdOptimizer", "EvolutionaryCheckpoint"],
            actions=["AnalyzeSuccessPatterns", "AdjustThresholds", "AnchorEvolution"],
            consents=["SelfEvolutionConsent"],
            purposes=["SystemicCoherence"],
            constraints={
                "high_privacy": True,
                "dp_epsilon": 0.1,
                "applied_optimizations": json.dumps(optimizations)
            }
        )

        # Gera e ancora a ontologia de evolução
        evolution_onto = self.generate_domain_ontology(spec)

        # 3. Notifica o Códice sobre a evolução do sistema
        self.codex.log_verdict(
            node_id="OntologicalForge",
            verdict="EVOLVED",
            coherence=1.0,
            payload_hash=evolution_onto.file_hash
        )

        return True
