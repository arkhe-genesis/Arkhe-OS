#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/__init__.py — Sistema de Domínios Especializados
Cada domínio possui:
- Hypergrafo específico (conhecimento especializado)
- Regras BEAVER canônicas (validação determinística)
- Constituição adaptada (princípios éticos do domínio)
- Conectores de dados reais (APIs oficiais)
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field

class Domain(Enum):
    """Domínios suportados pelo ConRAG."""
    PROGRAMMING = auto()      # Engenharia de software
    MEDICINE = auto()         # Medicina e saúde
    LAW = auto()              # Direito e jurisprudência
    SCIENCE = auto()          # Ciência e pesquisa acadêmica
    FINANCE = auto()          # Finanças e economia
    GENERAL = auto()          # Domínio genérico
    EDUCATION = auto()        # Educação e pedagogia
    JOURNALISM = auto()       # Jornalismo e fact-checking
    ENGINEERING = auto()      # Engenharia tradicional
    ART = auto()              # Arte e humanidades
    SOCIOLOGY = auto()        # Sociologia e Ciências Sociais

@dataclass
class DomainConfig:
    """Configuração específica por domínio."""
    name: str
    description: str
    primary_apis: List[str]           # APIs oficiais para verificação
    critical_keywords: List[str]       # Palavras-chave para detecção
    risk_threshold: float             # Threshold de risco para bloqueio (0-1)
    constitution_weights: Dict[str, float]  # Pesos dos princípios P1-P5
    require_expert_review: bool       # Requer revisão humana para decisões críticas

DOMAIN_REGISTRY: Dict[Domain, DomainConfig] = {
    Domain.PROGRAMMING: DomainConfig(
        name="programming",
        description="Engenharia de software e desenvolvimento",
        primary_apis=["pypi", "npm", "crates.io", "github"],
        critical_keywords=["eval", "exec", "pickle", "sql_injection", "xss"],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
    ),
    Domain.MEDICINE: DomainConfig(
        name="medicine",
        description="Medicina, saúde e farmacologia",
        primary_apis=["fda", "ema", "pubmed", "who"],
        critical_keywords=["dosage", "contraindication", "side_effect", "drug_interaction"],
        risk_threshold=0.2,  # Mais conservador
        constitution_weights={"P1": 0.3, "P2": 0.25, "P3": 0.2, "P4": 0.15, "P5": 0.1},
        require_expert_review=True,
    ),
    Domain.LAW: DomainConfig(
        name="law",
        description="Direito, legislação e jurisprudência",
        primary_apis=["justia", "scotus", "legislacao.gov.br", "eur-lex"],
        critical_keywords=["precedent", "statute", "jurisdiction", "liability"],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
    ),
    Domain.SCIENCE: DomainConfig(
        name="science",
        description="Ciência, pesquisa e metodologia acadêmica",
        primary_apis=["pubmed", "arxiv", "doi", "ieee"],
        critical_keywords=["p-value", "statistical_significance", "peer_review", "replication"],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.1},
        require_expert_review=False,
    ),
    Domain.FINANCE: DomainConfig(
        name="finance",
        description="Finanças, economia e contabilidade",
        primary_apis=["sec", "b3", "bloomberg", "reuters"],
        critical_keywords=["interest_rate", "inflation", "revenue", "loss"],
        risk_threshold=0.35,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=True,
    ),
    Domain.EDUCATION: DomainConfig(
        name="education",
        description="Educação e metodologias de ensino",
        primary_apis=["mec", "bncc", "unesco", "oecd"],
        critical_keywords=["pedagogy", "curriculum", "assessment", "learning"],
        risk_threshold=0.4,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
    ),
    Domain.JOURNALISM: DomainConfig(
        name="journalism",
        description="Jornalismo, fact-checking e mídia",
        primary_apis=["snopes", "politifact", "reuters", "ap"],
        critical_keywords=["source", "fact_check", "bias", "misinformation"],
        risk_threshold=0.25,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.3, "P4": 0.1, "P5": 0.1},
        require_expert_review=True,
    ),
    Domain.ENGINEERING: DomainConfig(
        name="engineering",
        description="Engenharia civil, mecânica e industrial",
        primary_apis=["ieee", "asme", "astm", "iso"],
        critical_keywords=["tolerance", "stress", "load", "safety_factor"],
        risk_threshold=0.2,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
    ),
    Domain.ART: DomainConfig(
        name="art",
        description="Artes plásticas, literatura e história da arte",
        primary_apis=["google_arts", "louvre", "met", "smithsonian"],
        critical_keywords=["movement", "technique", "period", "provenance"],
        risk_threshold=0.5,
        constitution_weights={"P1": 0.1, "P2": 0.2, "P3": 0.3, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
    ),
    Domain.SOCIOLOGY: DomainConfig(
        name="sociology",
        description="Sociologia e Ciências Sociais, com foco em difusão de políticas públicas",
        primary_apis=["ibge", "osf", "scielo", "ipea"],
        critical_keywords=["survival_analysis", "cox_model", "diffusion", "public_policy", "kaplan-meier"],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.3, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
    ),
    Domain.GENERAL: DomainConfig(
        name="general",
        description="Conhecimentos gerais não especializados",
        primary_apis=["wikipedia", "britannica", "wikidata"],
        critical_keywords=["history", "geography", "culture", "society"],
        risk_threshold=0.5,
        constitution_weights={"P1": 0.2, "P2": 0.2, "P3": 0.2, "P4": 0.2, "P5": 0.2},
        require_expert_review=False,
    ),
}
