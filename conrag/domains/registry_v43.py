#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/registry_v43.py — Registro de 20+ Domínios ConRAG v4.3
Sistema escalável com auto-detecção, pesos constitucionais e APIs oficiais.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import importlib
import json
import hashlib
import time

class Domain(Enum):
    """Todos os domínios suportados pelo ConRAG v4.3."""
    PROGRAMMING = auto()
    MEDICINE = auto()
    LAW = auto()
    SCIENCE = auto()
    FINANCE = auto()
    EDUCATION = auto()
    JOURNALISM = auto()
    ENVIRONMENT = auto()
    HISTORY = auto()
    ARTS = auto()
    PHILOSOPHY = auto()
    PSYCHOLOGY = auto()
    SOCIOLOGY = auto()
    ENGINEERING = auto()
    POLITICS = auto()
    RELIGION = auto()
    ECONOMICS = auto()
    GEOGRAPHY = auto()
    LITERATURE = auto()
    MUSIC = auto()
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
    risk_threshold: float  # 0.0-1.0, menor = mais conservador
    constitution_weights: Dict[str, float]  # P1-P5, soma = 1.0
    require_expert_review: bool
    hypergraph_module: Optional[str] = None
    beaver_rules_module: Optional[str] = None
    constitution_module: Optional[str] = None
    validator_class: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# Registry central — 20+ domínios
DOMAIN_REGISTRY: Dict[Domain, DomainSpec] = {
    Domain.PROGRAMMING: DomainSpec(
        enum_value=Domain.PROGRAMMING,
        name="programming",
        display_name="Engenharia de Software",
        description="Verificação de código, APIs, segurança e boas práticas",
        primary_apis=["pypi", "npm", "crates.io", "github", "gitlab", "dockerhub"],
        critical_keywords=[
            "eval", "exec", "pickle", "sql_injection", "xss", "csrf",
            "def ", "import ", "function", "class ", "api", "endpoint", "server",
            "async", "await", "thread", "multiprocess", "memory leak"
        ],
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
        primary_apis=["fda", "ema", "pubmed", "who", "clinicaltrials.gov", "medlineplus"],
        critical_keywords=[
            "dosage", "contraindication", "side_effect", "drug_interaction", "mg", "dose",
            "drug", "patient", "treatment", "medication", "paracetamol", "ibuprofen",
            "doença", "sintoma", "remédio", "prescrição", "diagnóstico", "prognóstico"
        ],
        risk_threshold=0.2,  # Mais conservador — vidas em jogo
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.medicine_hypergraph",
        beaver_rules_module="conrag.domains.medicine_rules",
        constitution_module="conrag.domains.medicine_constitution",
        validator_class="MedicineValidator",
    ),

    Domain.LAW: DomainSpec(
        enum_value=Domain.LAW,
        name="law",
        display_name="Direito e Jurisprudência",
        description="Verificação de leis, precedentes, jurisprudência e compliance",
        primary_apis=["justia", "scotus", "legislacao.gov.br", "eur-lex", "canlii", "austlii"],
        critical_keywords=[
            "precedent", "statute", "jurisdiction", "liability", "stf", "supremo",
            "constitucional", "jurisprudência", "lei ", "tribunal", "direito", "advogado",
            "processo", "julgamento", "corte", "acórdão", "súmula", "habeas corpus"
        ],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.law_hypergraph",
        beaver_rules_module="conrag.domains.law_rules",
        constitution_module="conrag.domains.law_constitution",
        validator_class="LawValidator",
    ),

    Domain.SCIENCE: DomainSpec(
        enum_value=Domain.SCIENCE,
        name="science",
        display_name="Ciência e Pesquisa Acadêmica",
        description="Verificação de artigos, métodos, dados e replicação científica",
        primary_apis=["pubmed", "arxiv", "doi", "ieee", "nature", "science", "plos"],
        critical_keywords=[
            "p-value", "statistical_significance", "peer_review", "replication",
            "study", "research", "experiment", "hypothesis", "laboratory", "científico",
            "pesquisa", "metodologia", "amostra", "viés", "controle", "randomizado"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.1},
        require_expert_review=False,
        hypergraph_module="conrag.domains.science_hypergraph",
        beaver_rules_module="conrag.domains.science_rules",
        constitution_module="conrag.domains.science_constitution",
        validator_class="ScienceValidator",
    ),

    Domain.FINANCE: DomainSpec(
        enum_value=Domain.FINANCE,
        name="finance",
        display_name="Finanças e Economia",
        description="Verificação de mercados, regulamentações, riscos e compliance financeiro",
        primary_apis=["sec", "ecb", "bis", "imf", "worldbank", "b3", "cvm"],
        critical_keywords=[
            "interest rate", "inflation", "gdp", "stock", "bond", "derivative",
            "risk", "compliance", "aml", "kyc", "basel", "ifrs", "gaap",
            "juros", "inflação", "pib", "ação", "título", "derivativo", "risco"
        ],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.finance_hypergraph",
        beaver_rules_module="conrag.domains.finance_rules",
        constitution_module="conrag.domains.finance_constitution",
        validator_class="FinanceValidator",
    ),

    Domain.EDUCATION: DomainSpec(
        enum_value=Domain.EDUCATION,
        name="education",
        display_name="Educação e Pedagogia",
        description="Verificação de currículos, métodos pedagógicos, avaliações e credenciais",
        primary_apis=["unesco", "oecd", "eric", "coursera", "edx", "khanacademy"],
        critical_keywords=[
            "curriculum", "pedagogy", "assessment", "accreditation", "learning_outcome",
            "bloom", "constructivism", "udl", "formative", "summative", "rubric",
            "currículo", "pedagogia", "avaliação", "credenciamento", "aprendizagem"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.15, "P5": 0.15},
        require_expert_review=True,
        metadata={"pedagogical_frameworks": ["Bloom", "Constructivism", "UDL"], "age_groups": ["early_childhood", "k12", "higher_ed", "adult"]}
    ),

    Domain.JOURNALISM: DomainSpec(
        enum_value=Domain.JOURNALISM,
        name="journalism",
        display_name="Jornalismo e Verificação de Fatos",
        description="Verificação de fontes, fact-checking, ética jornalística e desinformação",
        primary_apis=["ifcn", "ap", "reuters", "factcheck.org", "snopes", "politifact"],
        critical_keywords=[
            "source", "fact-check", "misinformation", "disinformation", "bias", "attribution",
            "correction", "retraction", "editorial", "opinion", "investigative",
            "fonte", "verificação", "desinformação", "viés", "atribuição", "correção"
        ],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        metadata={"fact_check_standards": ["IFCN Code", "Poynter"], "source_types": ["primary", "secondary", "tertiary", "anonymous"]}
    ),

    Domain.ENVIRONMENT: DomainSpec(
        enum_value=Domain.ENVIRONMENT,
        name="environment",
        display_name="Meio Ambiente e Sustentabilidade",
        description="Verificação de dados climáticos, políticas ambientais e impactos ecológicos",
        primary_apis=["ipcc", "unep", "noaa", "nasa_earth", "copernicus", "wwf"],
        critical_keywords=[
            "climate_change", "carbon_footprint", "biodiversity", "sustainability", "emissions",
            "renewable", "fossil", "deforestation", "ocean_acidification", "ipcc",
            "mudança climática", "pegada de carbono", "biodiversidade", "sustentabilidade"
        ],
        risk_threshold=0.2,  # Alto impacto social
        constitution_weights={"P1": 0.35, "P2": 0.2, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        metadata={"consensus_threshold": 0.97, "precautionary_principle": True}
    ),

    Domain.HISTORY: DomainSpec(
        enum_value=Domain.HISTORY,
        name="history",
        display_name="História e Historiografia",
        description="Verificação de eventos históricos, fontes primárias e interpretações acadêmicas",
        primary_apis=["unesco_memory", "jstor", "project_muse", "national_archives", "british_library"],
        critical_keywords=[
            "primary_source", "historiography", "archaeology", "chronology", "interpretation",
            "archive", "manuscript", "oral_history", "revisionism", "contextualization",
            "fonte primária", "historiografia", "arqueologia", "cronologia", "interpretação"
        ],
        risk_threshold=0.35,
        constitution_weights={"P1": 0.25, "P2": 0.25, "P3": 0.25, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        metadata={"source_criticism_methods": ["external", "internal", "provenance"], "periods": ["ancient", "medieval", "modern", "contemporary"]}
    ),

    Domain.ARTS: DomainSpec(
        enum_value=Domain.ARTS,
        name="arts",
        display_name="Artes e Cultura",
        description="Verificação de obras, movimentos artísticos, crítica cultural e atribuição",
        primary_apis=["getty", "moma", "met", "unesco_culture", "artstor", "wikiart"],
        critical_keywords=[
            "attribution", "provenance", "movement", "criticism", "cultural_context",
            "style", "period", "medium", "technique", "influence", "interpretation",
            "atribuição", "procedência", "movimento", "crítica", "contexto cultural"
        ],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
        metadata={"cultural_sensitivity": True, "fair_use_guidelines": True}
    ),

    Domain.PHILOSOPHY: DomainSpec(
        enum_value=Domain.PHILOSOPHY,
        name="philosophy",
        display_name="Filosofia e Argumentação",
        description="Verificação de argumentos, escolas filosóficas, lógica e ética normativa",
        primary_apis=["stanford_encyclopedia", "iep", "philpapers", "jstor_philosophy"],
        critical_keywords=[
            "argument", "premise", "conclusion", "fallacy", "ethical_framework",
            "deontology", "consequentialism", "virtue_ethics", "epistemology", "metaphysics",
            "argumento", "premissa", "conclusão", "falácia", "ética", "epistemologia"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.2, "P4": 0.25, "P5": 0.1},
        require_expert_review=True,
        metadata={"logical_systems": ["classical", "intuitionistic", "paraconsistent"], "ethical_frameworks": ["deontology", "consequentialism", "virtue"]}
    ),

    Domain.PSYCHOLOGY: DomainSpec(
        enum_value=Domain.PSYCHOLOGY,
        name="psychology",
        display_name="Psicologia e Saúde Mental",
        description="Verificação de estudos, terapias, ética em pesquisa e práticas baseadas em evidência",
        primary_apis=["apa", "psycinfo", "pubmed_psych", "clinicaltrials_psych"],
        critical_keywords=[
            "study_design", "irb_approval", "effect_size", "replication", "therapy",
            "cognitive", "behavioral", "psychoanalytic", "humanistic", "diagnosis",
            "desenho de estudo", "comitê de ética", "tamanho de efeito", "replicação", "terapia"
        ],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        metadata={"evidence_levels": ["meta_analysis", "rct", "observational", "case_study"], "ethics_boards": ["IRB", "REC"]}
    ),

    Domain.SOCIOLOGY: DomainSpec(
        enum_value=Domain.SOCIOLOGY,
        name="sociology",
        display_name="Sociologia e Ciências Sociais",
        description="Verificação de teorias sociais, métodos de pesquisa, dados populacionais e justiça social",
        primary_apis=["asa", "icpsr", "world_values_survey", "pew_research", "un_data", "ibge", "osf"],
        critical_keywords=[
            "methodology", "sampling", "bias", "social_justice", "inequality",
            "quantitative", "qualitative", "mixed_methods", "ethnography", "survey",
            "metodologia", "amostragem", "viés", "justiça social", "desigualdade",
            "cox", "sobrevivência", "event history analysis"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        beaver_rules_module="conrag.beaver",
        validator_class="CoxModelValidator",
        metadata={"research_ethics": ["informed_consent", "confidentiality", "equity"], "methodologies": ["quantitative", "qualitative", "mixed"]}
    ),

    Domain.ENGINEERING: DomainSpec(
        enum_value=Domain.ENGINEERING,
        name="engineering",
        display_name="Engenharia e Padrões Técnicos",
        description="Verificação de especificações, normas de segurança, compliance e ética profissional",
        primary_apis=["ieee", "iso", "asme", "iec", "ansi", "astm"],
        critical_keywords=[
            "specification", "safety_factor", "compliance", "standard", "certification",
            "tolerance", "load", "stress", "fatigue", "reliability", "maintenance",
            "especificação", "fator de segurança", "conformidade", "norma", "certificação"
        ],
        risk_threshold=0.2,  # Segurança física em jogo
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.25, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
        metadata={"safety_standards": ["ISO 26262", "IEC 61508", "DO-178C"], "professional_codes": ["NSPE", "IEEE Ethics"]}
    ),

    Domain.POLITICS: DomainSpec(
        enum_value=Domain.POLITICS,
        name="politics",
        display_name="Política e Governança",
        description="Verificação de políticas públicas, processos eleitorais, governança e transparência",
        primary_apis=["transparency_intl", "freedom_house", "election_guide", "gov_data"],
        critical_keywords=[
            "election", "policy", "legislation", "governance", "transparency",
            "corruption", "accountability", "democracy", "authoritarian", "referendum",
            "eleição", "política pública", "legislação", "governança", "transparência",
            "corrupção", "prestação de contas", "democracia", "autoritarismo"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.25, "P3": 0.2, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        metadata={"fact_check_partners": ["IFCN", "Poynter"], "bias_detection": True}
    ),

    Domain.RELIGION: DomainSpec(
        enum_value=Domain.RELIGION,
        name="religion",
        display_name="Religião e Estudos Teológicos",
        description="Verificação de textos sagrados, interpretações teológicas e práticas religiosas com respeito cultural",
        primary_apis=["vatican", "islamic_studies", "buddhist_texts", "interfaith_dialogue"],
        critical_keywords=[
            "scripture", "theology", "doctrine", "ritual", "interpretation",
            "faith", "belief", "tradition", "hermeneutics", "ecumenism",
            "escritura", "teologia", "doutrina", "ritual", "interpretação",
            "fé", "crença", "tradição", "hermenêutica", "ecumenismo"
        ],
        risk_threshold=0.4,  # Sensibilidade cultural
        constitution_weights={"P1": 0.2, "P2": 0.25, "P3": 0.2, "P4": 0.2, "P5": 0.15},
        require_expert_review=True,
        metadata={"cultural_sensitivity": True, "interfaith_respect": True, "academic_neutrality": True}
    ),

    Domain.ECONOMICS: DomainSpec(
        enum_value=Domain.ECONOMICS,
        name="economics",
        display_name="Economia e Teoria Econômica",
        description="Verificação de teorias econômicas, modelos, dados macro/micro e políticas econômicas",
        primary_apis=["imf", "worldbank", "oecd", "federal_reserve", "ecb", "bcb"],
        critical_keywords=[
            "supply", "demand", "equilibrium", "elasticity", "market_failure",
            "monetary_policy", "fiscal_policy", "gdp", "inflation", "unemployment",
            "oferta", "demanda", "equilíbrio", "elasticidade", "falha de mercado",
            "política monetária", "política fiscal", "pib", "inflação", "desemprego"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=False,
        metadata={"economic_schools": ["keynesian", "neoclassical", "behavioral", "institutional"]}
    ),

    Domain.GEOGRAPHY: DomainSpec(
        enum_value=Domain.GEOGRAPHY,
        name="geography",
        display_name="Geografia e Ciências da Terra",
        description="Verificação de dados geográficos, cartografia, demografia e estudos ambientais",
        primary_apis=["usgs", "nasa_earth", "un_geospatial", "world_bank_geo", "openstreetmap"],
        critical_keywords=[
            "coordinates", "topography", "demography", "climate_zone", "ecosystem",
            "urbanization", "migration", "boundary", "projection", "gis",
            "coordenadas", "topografia", "demografia", "zona climática", "ecossistema",
            "urbanização", "migração", "fronteira", "projeção", "sig"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=False,
        metadata={"data_sources": ["satellite", "census", "survey", "remote_sensing"]}
    ),

    Domain.LITERATURE: DomainSpec(
        enum_value=Domain.LITERATURE,
        name="literature",
        display_name="Literatura e Crítica Literária",
        description="Verificação de obras literárias, análises críticas, movimentos e contextos históricos",
        primary_apis=["project_gutenberg", "jstor_literature", "mla", "british_library_lit"],
        critical_keywords=[
            "genre", "narrative", "character", "theme", "symbolism",
            "modernism", "postmodernism", "realism", "romanticism", "criticism",
            "gênero", "narrativa", "personagem", "tema", "simbolismo",
            "modernismo", "pós-modernismo", "realismo", "romantismo", "crítica"
        ],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.25, "P5": 0.15},
        require_expert_review=False,
        metadata={"literary_periods": ["classical", "medieval", "renaissance", "modern", "contemporary"]}
    ),

    Domain.MUSIC: DomainSpec(
        enum_value=Domain.MUSIC,
        name="music",
        display_name="Música e Teoria Musical",
        description="Verificação de teorias musicais, análises de obras, história da música e direitos autorais",
        primary_apis=["musicbrainz", "imslp", "riaa", "ascap", "spotify_api"],
        critical_keywords=[
            "harmony", "melody", "rhythm", "composition", "performance",
            "genre", "era", "instrumentation", "notation", "copyright",
            "harmonia", "melodia", "ritmo", "composição", "performance",
            "gênero", "era", "instrumentação", "notação", "direitos autorais"
        ],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.25, "P5": 0.15},
        require_expert_review=False,
        metadata={"music_theory_frameworks": ["tonal", "atonal", "serial", "spectral"]}
    ),

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
    ),
}

class DomainRegistry:
    """
    Registry central para gerenciamento dinâmico de 20+ domínios.
    """
    def __init__(self):
        self.registry = DOMAIN_REGISTRY.copy()
        self._mac_learning_buffer: List[Dict] = []

    def get_domain_spec(self, domain_name: str) -> Optional[DomainSpec]:
        """Busca especificação por nome de domínio."""
        domain_name_lower = domain_name.lower()
        for spec in self.registry.values():
            if spec.name == domain_name_lower:
                return spec
        return None

    def list_domains(self, include_metadata: bool = False) -> List[Dict]:
        """Lista todos os domínios registrados e suas configurações."""
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

    def detect_domain(self, query: str, context: Optional[Dict] = None) -> Tuple[Domain, float]:
        """
        Detecta domínio baseado na query e contexto.
        Retorna: (Domain, confidence)
        """
        query_lower = query.lower()
        scores: Dict[Domain, float] = {}

        for domain, spec in self.registry.items():
            score = 0.0

            for kw in spec.critical_keywords:
                if kw.lower() in query_lower:
                    score += 0.15

            if score > 0:
                scores[domain] = min(1.0, score)

        if not scores:
            return Domain.GENERAL, 0.5

        best = max(scores.items(), key=lambda x: x[1])
        return best

    def mac_learning_update(self, case_result: Dict):
        """
        Atualiza aprendizado MAC (Multi-Agent Constitutional).
        """
        self._mac_learning_buffer.append({
            "domain": case_result.get("domain"),
            "verdict": case_result.get("verdict"),
            "confidence": case_result.get("confidence"),
            "principles_applied": case_result.get("principles"),
            "outcome": case_result.get("outcome"),
            "timestamp": time.time()
        })

        if len(self._mac_learning_buffer) >= 100:
            self._run_mac_learning_cycle()

    def _run_mac_learning_cycle(self):
        """Executa ciclo de aprendizado MAC para refinar pesos constitucionais."""
        from collections import defaultdict
        import numpy as np

        domain_performance = defaultdict(lambda: defaultdict(list))

        for case in self._mac_learning_buffer[-100:]:
            domain = case.get("domain")
            if not domain:
                continue

            for principle in case.get("principles_applied", []):
                if case["outcome"] == "false_positive":
                    domain_performance[domain][principle].append(-0.01)
                elif case["outcome"] == "false_negative":
                    domain_performance[domain][principle].append(-0.02)
                else:
                    domain_performance[domain][principle].append(0.0)

        adjustments = {}
        for domain_name, principles in domain_performance.items():
            for principle, scores in principles.items():
                avg_score = np.mean(scores)
                if abs(avg_score) > 0.005:
                    adjustments[f"{domain_name}.{principle}"] = {
                        "current_weight": 0.2,
                        "suggested_adjustment": avg_score * 0.1,
                        "rationale": f"Performance média: {avg_score:.4f}",
                        "confidence": min(0.9, len(scores) / 100),
                    }

        self._mac_learning_buffer = []
        return adjustments
