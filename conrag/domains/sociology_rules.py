#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology_rules.py — Regras BEAVER para Domínio Sociologia
Validação determinística para modelos estatísticos (ex. Event History Analysis).
"""

from typing import Tuple, Dict, Any

class SociologyBEAVERRules:
    """
    Regras BEAVER especializadas para sociologia e políticas públicas.
    Inclui o CoxModelValidator.
    """

    RULES = {
        "proportional_hazards": {
            "description": "Riscos proporcionais (Cox) não devem ser violados",
            "check": "_check_proportional_hazards",
            "severity": "block",
        },
        "multicollinearity_vif": {
            "description": "Multicolinearidade (VIF) não deve exceder limite",
            "check": "_check_multicollinearity",
            "severity": "block",
        },
        "linearity": {
            "description": "Covariáveis contínuas devem manter linearidade",
            "check": "_check_linearity",
            "severity": "warn",
        },
        "independence": {
            "description": "Observações devem ser independentes",
            "check": "_check_independence",
            "severity": "warn",
        },
    }

    @staticmethod
    def _check_proportional_hazards(p_value: float, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica a suposição de riscos proporcionais para o modelo de Cox.
        O p-valor de testes (ex. Schoenfeld residuals) deve ser > 0.05.
        """
        if p_value > 0.05:
            return True, "OK (Riscos proporcionais validados)"
        return False, f"Violação de riscos proporcionais detectada (p-valor: {p_value} <= 0.05)"

    @staticmethod
    def _check_multicollinearity(vif_value: float, limit: float = 5.0, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica a ausência de multicolinearidade.
        O VIF (Variance Inflation Factor) não deve exceder o limite (default 5.0).
        """
        if vif_value < limit:
            return True, "OK (VIF dentro dos limites aceitáveis)"
        return False, f"Alta multicolinearidade detectada (VIF: {vif_value} >= {limit})"

    @staticmethod
    def _check_linearity(is_linear: bool, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica a linearidade das covariáveis contínuas.
        """
        if is_linear:
            return True, "OK (Linearidade confirmada)"
        return False, "Violação da suposição de linearidade para covariáveis contínuas"

    @staticmethod
    def _check_independence(is_independent: bool, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica se as observações (e tempos de evento) são independentes.
        """
        if is_independent:
            return True, "OK (Independência confirmada)"
        return False, "Violação de independência nas observações"

class CoxModelValidator:
    """
    Validador específico para modelos de Cox, delegando para SociologyBEAVERRules.
    """

    @staticmethod
    def validate_model(p_value: float, max_vif: float, is_linear: bool, is_independent: bool) -> Dict[str, Any]:
        """
        Valida todas as suposições chave do modelo de Cox.
        Retorna um dicionário com os resultados de cada teste.
        """
        results = {
            "proportional_hazards": SociologyBEAVERRules._check_proportional_hazards(p_value),
            "multicollinearity": SociologyBEAVERRules._check_multicollinearity(max_vif),
            "linearity": SociologyBEAVERRules._check_linearity(is_linear),
            "independence": SociologyBEAVERRules._check_independence(is_independent),
        }

        all_passed = all(res[0] for res in results.values())
        return {
            "is_valid": all_passed,
            "details": results
        }
