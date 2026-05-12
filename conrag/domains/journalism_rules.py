#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/journalism_rules.py — Regras BEAVER para Jornalismo
Validação determinística baseada em ética jornalística e fact-checking.
"""

from typing import Tuple, Dict, List
import re

class JournalismBEAVERRules:
    """
    Regras BEAVER especializadas para jornalismo.
    Cada regra é verificável deterministicamente via APIs de fact-checking.
    """

    RULES = {
        "source_verified": {
            "description": "Fonte deve ser verificável e confiável",
            "check": "_check_source_verified",
            "severity": "block",
        },
        "fact_checked": {
            "description": "Afirmação factual deve ter verificação independente",
            "check": "_check_fact_verified",
            "severity": "block",
        },
        "bias_disclosed": {
            "description": "Viés ou conflito de interesse deve ser declarado",
            "check": "_check_bias_disclosed",
            "severity": "warn",
        },
        "attribution_complete": {
            "description": "Citações devem ter atribuição completa",
            "check": "_check_attribution",
            "severity": "warn",
        },
        "misinformation_flag": {
            "description": "Alertar sobre conteúdo marcado como desinformação",
            "check": "_check_misinformation",
            "severity": "block",
        },
    }

    @staticmethod
    def _check_source_verified(claim: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se fonte é confiável (via IFCN, AP, Reuters)."""
        # Em produção: consultar APIs de fact-checking
        trusted_sources = ["ap.org", "reuters.com", "bbc.com", "nytimes.com", "washingtonpost.com"]
        source = context.get("source_url", "").lower()

        if any(ts in source for ts in trusted_sources):
            return True, "OK"
        return False, f"Fonte não verificada: {source}"

    @staticmethod
    def _check_fact_verified(claim: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se afirmação foi fact-checkada."""
        # Em produção: consultar Snopes, FactCheck.org, PolitiFact
        fact_checked_claims = ["vaccine efficacy", "election results", "climate data"]
        if any(fc in claim.lower() for fc in fact_checked_claims):
            return True, "OK (fact-checked)"
        return False, "Afirmação factual sem verificação independente"

    @staticmethod
    def _check_bias_disclosed(claim: str, context: Dict) -> Tuple[bool, str]:
        """Verifica declaração de viés ou conflito."""
        if context.get("bias_disclosed", False):
            return True, "OK"
        # Verificar texto por indicadores de viés não declarado
        bias_indicators = ["in my opinion", "clearly", "obviously", "everyone knows"]
        if any(bi in claim.lower() for bi in bias_indicators):
            return False, "Viés potencial não declarado"
        return True, "OK"

    @staticmethod
    def _check_attribution(claim: str, context: Dict) -> Tuple[bool, str]:
        """Verifica atribuição completa de citações."""
        # Verificar padrão de citação: "..." said X or according to X
        if re.search(r'["\'][^"\']+["\']\s+(said|according to|per)\s+\w+', claim, re.I):
            return True, "OK"
        return False, "Citação sem atribuição clara"

    @staticmethod
    def _check_misinformation(claim: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se conteúdo foi marcado como desinformação."""
        # Em produção: consultar bases de desinformação
        known_misinfo = ["pizzagate", "vaccine microchips", "election fraud 2020"]
        if any(mi in claim.lower() for mi in known_misinfo):
            return False, "Conteúdo marcado como desinformação"
        return True, "OK"
