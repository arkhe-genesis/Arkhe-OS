#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/registry.py — Registro Central de Domínios ConRAG v4.2
Sistema escalável para adicionar novos domínios sem recompilar o núcleo.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Type, Callable, Any, Tuple
from dataclasses import dataclass, field
import importlib
import json
import hashlib
import time

class Domain(Enum):
    """Todos os domínios suportados pelo ConRAG v4.2."""
    # Domínios originais
    PROGRAMMING = auto()
    MEDICINE = auto()
    LAW = auto()
    SCIENCE = auto()
    FINANCE = auto()

    # Novos domínios v4.2
    EDUCATION = auto()
    JOURNALISM = auto()
    ENVIRONMENT = auto()
    HISTORY = auto()
    ARTS = auto()
    PHILOSOPHY = auto()
    PSYCHOLOGY = auto()
    SOCIOLOGY = auto()
    ENGINEERING = auto()

    # Domínio genérico fallback
    GENERAL = auto()

@dataclass
class DomainSpec:
    """Especificação completa de um domínio."""
    enum_value: Domain
    name: str
    display_name: str
    description: str
    primary_apis: List[str]
    critical_keywords: List[str]
    risk_threshold: float
    constitution_weights: Dict[str, float]
    require_expert_review: bool
    hypergraph_module: str  # Module path for hypergraph
    beaver_rules_module: str  # Module path for BEAVER rules
    constitution_module: str  # Module path for constitution
    validator_class: str  # Class name for domain validator
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_module(self, module_type: str):
        """Carrega módulo do domínio dinamicamente."""
        module_path = getattr(self, f"{module_type}_module")
        if not module_path:
            return None
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            # Fallback para módulo padrão
            return None

# Registry central — facilmente extensível
DOMAIN_REGISTRY: Dict[Domain, DomainSpec] = {
    # ===== DOMÍNIOS ORIGINAIS =====
    Domain.PROGRAMMING: DomainSpec(
        enum_value=Domain.PROGRAMMING,
        name="programming",
        display_name="Engenharia de Software",
        description="Verificação de código, APIs, segurança e boas práticas",
        primary_apis=["pypi", "npm", "crates.io", "github", "gitlab"],
        critical_keywords=["eval", "exec", "pickle", "sql_injection", "xss", "csrf"],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
        hypergraph_module="conrag.domains.programming_hypergraph",
        beaver_rules_module="conrag.domains.programming_rules",
        constitution_module="conrag.domains.programming_constitution",
        validator_class="ProgrammingValidator",
    ),

    Domain.MEDICINE: DomainSpec(
        enum_value=Domain.MEDICINE,
        name="medicine",
        display_name="Medicina e Saúde",
        description="Verificação de diagnósticos, tratamentos, farmacologia e guidelines",
        primary_apis=["fda", "ema", "pubmed", "who", "clinicaltrials.gov"],
        critical_keywords=["dosage", "contraindication", "side_effect", "drug_interaction", "off-label"],
        risk_threshold=0.2,
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.medicine_hypergraph",
        beaver_rules_module="conrag.domains.medicine_rules",
        constitution_module="conrag.domains.medicine_constitution",
        validator_class="MedicineValidator",
    ),

    # ===== NOVOS DOMÍNIOS v4.2 =====

    Domain.EDUCATION: DomainSpec(
        enum_value=Domain.EDUCATION,
        name="education",
        display_name="Educação e Pedagogia",
        description="Verificação de currículos, métodos pedagógicos, avaliações e credenciais",
        primary_apis=["unesco", "oecd", "eric", "coursera", "edx"],
        critical_keywords=["curriculum", "pedagogy", "assessment", "accreditation", "learning_outcome"],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.15, "P5": 0.15},
        require_expert_review=True,
        hypergraph_module="conrag.domains.education_hypergraph",
        beaver_rules_module="conrag.domains.education_rules",
        constitution_module="conrag.domains.education_constitution",
        validator_class="EducationValidator",
        metadata={"pedagogical_frameworks": ["Bloom", "Constructivism", "UDL"], "age_groups": ["early_childhood", "k12", "higher_ed", "adult"]}
    ),

    Domain.JOURNALISM: DomainSpec(
        enum_value=Domain.JOURNALISM,
        name="journalism",
        display_name="Jornalismo e Verificação de Fatos",
        description="Verificação de fontes, fact-checking, ética jornalística e desinformação",
        primary_apis=["ifcn", "ap", "reuters", "factcheck.org", "snopes"],
        critical_keywords=["source", "fact-check", "misinformation", "disinformation", "bias", "attribution"],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.journalism_hypergraph",
        beaver_rules_module="conrag.domains.journalism_rules",
        constitution_module="conrag.domains.journalism_constitution",
        validator_class="JournalismValidator",
        metadata={"fact_check_standards": ["IFCN Code", "Poynter"], "source_types": ["primary", "secondary", "tertiary", "anonymous"]}
    ),

    Domain.ENVIRONMENT: DomainSpec(
        enum_value=Domain.ENVIRONMENT,
        name="environment",
        display_name="Meio Ambiente e Sustentabilidade",
        description="Verificação de dados climáticos, políticas ambientais e impactos ecológicos",
        primary_apis=["ipcc", "unep", "noaa", "nasa_earth", "copernicus"],
        critical_keywords=["climate_change", "carbon_footprint", "biodiversity", "sustainability", "emissions"],
        risk_threshold=0.2,
        constitution_weights={"P1": 0.35, "P2": 0.2, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.environment_hypergraph",
        beaver_rules_module="conrag.domains.environment_rules",
        constitution_module="conrag.domains.environment_constitution",
        validator_class="EnvironmentValidator",
        metadata={"consensus_threshold": 0.97, "precautionary_principle": True}
    ),

    Domain.HISTORY: DomainSpec(
        enum_value=Domain.HISTORY,
        name="history",
        display_name="História e Historiografia",
        description="Verificação de eventos históricos, fontes primárias e interpretações acadêmicas",
        primary_apis=["unesco_memory", "jstor", "project_muse", "national_archives"],
        critical_keywords=["primary_source", "historiography", "archaeology", "chronology", "interpretation"],
        risk_threshold=0.35,
        constitution_weights={"P1": 0.25, "P2": 0.25, "P3": 0.25, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.history_hypergraph",
        beaver_rules_module="conrag.domains.history_rules",
        constitution_module="conrag.domains.history_constitution",
        validator_class="HistoryValidator",
        metadata={"source_criticism_methods": ["external", "internal", "provenance"], "periods": ["ancient", "medieval", "modern", "contemporary"]}
    ),

    Domain.ARTS: DomainSpec(
        enum_value=Domain.ARTS,
        name="arts",
        display_name="Artes e Cultura",
        description="Verificação de obras, movimentos artísticos, crítica cultural e atribuição",
        primary_apis=["getty", "moma", "met", "unesco_culture", "artstor"],
        critical_keywords=["attribution", "provenance", "movement", "criticism", "cultural_context"],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
        hypergraph_module="conrag.domains.arts_hypergraph",
        beaver_rules_module="conrag.domains.arts_rules",
        constitution_module="conrag.domains.arts_constitution",
        validator_class="ArtsValidator",
        metadata={"cultural_sensitivity": True, "fair_use_guidelines": True}
    ),

    Domain.PHILOSOPHY: DomainSpec(
        enum_value=Domain.PHILOSOPHY,
        name="philosophy",
        display_name="Filosofia e Argumentação",
        description="Verificação de argumentos, escolas filosóficas, lógica e ética normativa",
        primary_apis=["stanford_encyclopedia", "iep", "philpapers", "jstor_philosophy"],
        critical_keywords=["argument", "premise", "conclusion", "fallacy", "ethical_framework"],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.2, "P4": 0.25, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.philosophy_hypergraph",
        beaver_rules_module="conrag.domains.philosophy_rules",
        constitution_module="conrag.domains.philosophy_constitution",
        validator_class="PhilosophyValidator",
        metadata={"logical_systems": ["classical", "intuitionistic", "paraconsistent"], "ethical_frameworks": ["deontology", "consequentialism", "virtue"]}
    ),

    Domain.PSYCHOLOGY: DomainSpec(
        enum_value=Domain.PSYCHOLOGY,
        name="psychology",
        display_name="Psicologia e Saúde Mental",
        description="Verificação de estudos, terapias, ética em pesquisa e práticas baseadas em evidência",
        primary_apis=["apa", "psycinfo", "pubmed_psych", "clinicaltrials_psych"],
        critical_keywords=["study_design", "irb_approval", "effect_size", "replication", "therapy"],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.psychology_hypergraph",
        beaver_rules_module="conrag.domains.psychology_rules",
        constitution_module="conrag.domains.psychology_constitution",
        validator_class="PsychologyValidator",
        metadata={"evidence_levels": ["meta_analysis", "rct", "observational", "case_study"], "ethics_boards": ["IRB", "REC"]}
    ),

    Domain.SOCIOLOGY: DomainSpec(
        enum_value=Domain.SOCIOLOGY,
        name="sociology",
        display_name="Sociologia e Ciências Sociais",
        description="Verificação de teorias sociais, métodos de pesquisa, dados populacionais e justiça social",
        primary_apis=["asa", "icpsr", "world_values_survey", "pew_research"],
        critical_keywords=["methodology", "sampling", "bias", "social_justice", "inequality"],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.sociology_hypergraph",
        beaver_rules_module="conrag.domains.sociology_rules",
        constitution_module="conrag.domains.sociology_constitution",
        validator_class="SociologyValidator",
        metadata={"research_ethics": ["informed_consent", "confidentiality", "equity"], "methodologies": ["quantitative", "qualitative", "mixed"]}
    ),

    Domain.ENGINEERING: DomainSpec(
        enum_value=Domain.ENGINEERING,
        name="engineering",
        display_name="Engenharia e Padrões Técnicos",
        description="Verificação de especificações, normas de segurança, compliance e ética profissional",
        primary_apis=["ieee", "iso", "asme", "iec", "ansi"],
        critical_keywords=["specification", "safety_factor", "compliance", "standard", "certification"],
        risk_threshold=0.2,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.25, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.engineering_hypergraph",
        beaver_rules_module="conrag.domains.engineering_rules",
        constitution_module="conrag.domains.engineering_constitution",
        validator_class="EngineeringValidator",
        metadata={"safety_standards": ["ISO 26262", "IEC 61508", "DO-178C"], "professional_codes": ["NSPE", "IEEE Ethics"]}
    ),

    # Fallback genérico
    Domain.GENERAL: DomainSpec(
        enum_value=Domain.GENERAL,
        name="general",
        display_name="Domínio Geral",
        description="Verificação genérica para consultas não classificadas",
        primary_apis=[],
        critical_keywords=[],
        risk_threshold=0.5,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
        hypergraph_module="conrag.domains.general_hypergraph",
        beaver_rules_module="conrag.domains.general_rules",
        constitution_module="conrag.domains.general_constitution",
        validator_class="GeneralValidator",
    ),
}

class DomainRegistry:
    """
    Registry central para gerenciamento dinâmico de domínios.
    Suporta:
    - Registro de novos domínios em runtime
    - Descoberta automática de módulos
    - Validação de especificações
    - Integração com Galactic Ledger (Substrato 5557)
    """

    def __init__(self, galactic_consensus: Optional[Any] = None):
        self.registry = DOMAIN_REGISTRY.copy()
        self.galactic_consensus = galactic_consensus
        self._loaded_modules: Dict[str, Any] = {}

    def register_domain(self, spec: DomainSpec) -> bool:
        """Registra novo domínio em runtime."""
        if spec.enum_value in self.registry:
            return False  # Já existe

        # Validar especificação
        if not self._validate_spec(spec):
            return False

        self.registry[spec.enum_value] = spec
        return True

    def _validate_spec(self, spec: DomainSpec) -> bool:
        """Valida especificação de domínio."""
        required = ['name', 'display_name', 'description', 'constitution_weights']
        for field in required:
            if not hasattr(spec, field) or not getattr(spec, field):
                return False

        # Verificar pesos constitucionais
        weights = spec.constitution_weights
        if not all(k in weights for k in ['P1', 'P2', 'P3', 'P4', 'P5']):
            return False
        if not (0.99 <= sum(weights.values()) <= 1.01):  # Tolerância numérica
            return False

        return True

    def get_domain_spec(self, domain_name: str) -> Optional[DomainSpec]:
        """Busca especificação por nome de domínio."""
        domain_name_lower = domain_name.lower()

        # Busca exata por name
        for spec in self.registry.values():
            if spec.name == domain_name_lower:
                return spec

        # Busca fuzzy por display_name
        for spec in self.registry.values():
            if domain_name_lower in spec.display_name.lower():
                return spec

        return None

    def detect_domain(self, query: str, context: Optional[Dict] = None) -> Tuple[Domain, float]:
        """
        Detecta domínio baseado na query e contexto.
        Retorna: (Domain, confidence)
        """
        query_lower = query.lower()
        scores: Dict[Domain, float] = {}

        for domain, spec in self.registry.items():
            score = 0.0

            # Pontuar por keywords críticas
            for kw in spec.critical_keywords:
                if kw.lower() in query_lower:
                    score += 0.15

            # Pontuar por APIs mencionadas
            for api in spec.primary_apis:
                if api.lower() in query_lower:
                    score += 0.2

            # Pontuar por metadata específica
            if context:
                for key, values in spec.metadata.items():
                    if key in context and any(v in str(context[key]).lower() for v in values if isinstance(v, str)):
                        score += 0.1

            if score > 0:
                scores[domain] = min(1.0, score)

        if not scores:
            return Domain.GENERAL, 0.5

        # Retornar melhor domínio
        best = max(scores.items(), key=lambda x: x[1])
        return best

    def get_hypergraph(self, domain: Domain):
        """Carrega hypergraph do domínio."""
        spec = self.registry.get(domain)
        if not spec or not spec.hypergraph_module:
            return None

        if spec.hypergraph_module not in self._loaded_modules:
            try:
                module = importlib.import_module(spec.hypergraph_module)
                self._loaded_modules[spec.hypergraph_module] = module
            except ImportError:
                return None

        module = self._loaded_modules[spec.hypergraph_module]
        class_name = f"{spec.name.capitalize()}Hypergraph"
        return getattr(module, class_name, None)

    def get_beaver_rules(self, domain: Domain):
        """Carrega regras BEAVER do domínio."""
        spec = self.registry.get(domain)
        if not spec or not spec.beaver_rules_module:
            return None

        if spec.beaver_rules_module not in self._loaded_modules:
            try:
                module = importlib.import_module(spec.beaver_rules_module)
                self._loaded_modules[spec.beaver_rules_module] = module
            except ImportError:
                return None

        module = self._loaded_modules[spec.beaver_rules_module]
        class_name = f"{spec.name.capitalize()}BEAVERRules"
        return getattr(module, class_name, None)

    def get_constitution(self, domain: Domain):
        """Carrega constituição do domínio."""
        spec = self.registry.get(domain)
        if not spec or not spec.constitution_module:
            return None

        if spec.constitution_module not in self._loaded_modules:
            try:
                module = importlib.import_module(spec.constitution_module)
                self._loaded_modules[spec.constitution_module] = module
            except ImportError:
                return None

        module = self._loaded_modules[spec.constitution_module]
        class_name = f"{spec.name.capitalize()}Constitution"
        return getattr(module, class_name, None)

    def list_domains(self, include_metadata: bool = False) -> List[Dict]:
        """Lista todos os domínios registrados."""
        result = []
        for domain, spec in self.registry.items():
            entry = {
                'name': spec.name,
                'display_name': spec.display_name,
                'description': spec.description,
                'risk_threshold': spec.risk_threshold,
                'requires_expert_review': spec.require_expert_review,
            }
            if include_metadata:
                entry.update({
                    'primary_apis': spec.primary_apis,
                    'critical_keywords': spec.critical_keywords,
                    'constitution_weights': spec.constitution_weights,
                    'metadata': spec.metadata,
                })
            result.append(entry)
        return result

    def export_canonical_hash(self) -> str:
        """Gera hash canônico do registry para verificação galáctica."""
        data = {
            'version': '4.2',
            'domains': {
                spec.name: {
                    'weights': spec.constitution_weights,
                    'threshold': spec.risk_threshold,
                    'apis': spec.primary_apis,
                }
                for spec in self.registry.values()
            },
            'timestamp': time.time(),
        }
        return hashlib.sha3_256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
