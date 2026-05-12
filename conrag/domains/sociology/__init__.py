#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/__init__.py — Domínio Sociology com Cox Model Validator
"""

from .cox_validator import (
    CoxAssumption,
    CoxValidationResult,
    CoxModelReport,
    IBGEDataConnector,
    OSFDataConnector,
    CoxAssumptionValidator,
    CoxModelValidator,
    SociologyBEAVERRules,
)

__all__ = [
    "CoxAssumption",
    "CoxValidationResult",
    "CoxModelReport",
    "IBGEDataConnector",
    "OSFDataConnector",
    "CoxAssumptionValidator",
    "CoxModelValidator",
    "SociologyBEAVERRules",
]

# Registrar automaticamente no DomainRegistry
def register_sociology_domain(registry):
    """Registra domínio Sociology no DomainRegistry global."""
    from conrag.domains.registry import Domain, DomainSpec

    spec = DomainSpec(
        enum_value=Domain.SOCIOLOGY,
        name="sociology",
        display_name="Sociologia e Ciências Sociais",
        description="Verificação de teorias sociais, métodos de pesquisa, dados populacionais, justiça social e difusão de políticas públicas",
        primary_apis=["asa", "icpsr", "world_values_survey", "pew_research", "un_data", "ibge", "osf"],
        critical_keywords=[
            "methodology", "sampling", "bias", "social_justice", "inequality",
            "quantitative", "qualitative", "mixed_methods", "ethnography", "survey",
            "policy_diffusion", "survival_analysis", "cox_model", "event_history",
            "metodologia", "amostragem", "viés", "justiça social", "desigualdade",
            "difusão de políticas", "análise de sobrevivência", "modelo de cox"
        ],
        risk_threshold=0.3,
        constitution_weights={"P1": 0.25, "P2": 0.2, "P3": 0.25, "P4": 0.2, "P5": 0.1},
        require_expert_review=True,
        hypergraph_module="conrag.domains.sociology_hypergraph",
        beaver_rules_module="conrag.domains.sociology_rules",  # Inclui CoxModelValidator
        constitution_module="conrag.domains.sociology_constitution",
        validator_class="SociologyValidator",
        metadata={
            "research_ethics": ["informed_consent", "confidentiality", "equity"],
            "methodologies": ["quantitative", "qualitative", "mixed", "survival_analysis"],
            "data_sources": ["IBGE", "OSF", "ICPSR", "Pew", "UN"],
            "statistical_models": ["cox_regression", "kaplan_meier", "logistic_regression", "multilevel"],
        },
    )

    return registry.register_domain(spec)
