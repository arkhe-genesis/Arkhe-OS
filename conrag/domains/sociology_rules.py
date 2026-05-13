#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology_rules.py — Regras BEAVER para Domínio Sociologia
Validação determinística para modelos estatísticos (ex. Event History Analysis).
"""

import time
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass

from conrag.domains.sociology.ibge_cache import IBGECacheManager
from conrag.domains.sociology.frailty_models import FrailtyCoxModel
from conrag.domains.sociology.r_bridge import RSurvivalAnalyzer
from conrag.domains.sociology.visualizations import CanonicalVisualizer
from conrag.domains.sociology.expanded_models import ExpandedSociologyModels

@dataclass
class CoxModelReport:
    dataset_name: str
    n_observations: int
    n_events: int
    n_censored: int
    covariates: List[str]
    results: Dict[str, Any]
    overall_valid: bool
    canonical_seal: str
    timestamp: float
    data_source: str
    visualizations: List[str]
    cache_stats: Dict[str, Any]

try:
    from .sociology.cox_validator import SociologyBEAVERRules as NewSociologyBEAVERRules, CoxModelValidator as NewCoxModelValidator
except ImportError:
    NewSociologyBEAVERRules = None
    NewCoxModelValidator = None

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
        "homogeneous_distribution": {
            "description": "A distribuição dos eventos deve ser homogênea",
            "check": "_check_homogeneous_distribution",
            "severity": "warn",
        },
        "time_independence": {
            "description": "Os tempos de evento devem ser independentes",
            "check": "_check_time_independence",
            "severity": "block",
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
        Verifica se as observações são independentes.
        """
        if is_independent:
            return True, "OK (Independência confirmada)"
        return False, "Violação de independência nas observações"

    @staticmethod
    def _check_homogeneous_distribution(is_homogeneous: bool, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica se a distribuição de eventos/censuras é homogênea ao longo do tempo.
        """
        if is_homogeneous:
            return True, "OK (Distribuição homogênea confirmada)"
        return False, "Violação de distribuição homogênea"

    @staticmethod
    def _check_time_independence(is_time_independent: bool, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Verifica se os tempos de censura são independentes do tempo de evento.
        """
        if is_time_independent:
            return True, "OK (Independência dos tempos confirmada)"
        return False, "Violação de independência dos tempos de censura"

class CoxModelValidator:
    def __init__(
        self,
        hypergraph=None,
        audit_logger=None,
        cache_manager: Optional[IBGECacheManager] = None,
        r_analyzer: Optional[RSurvivalAnalyzer] = None,
        use_frailty: bool = True,
        generate_plots: bool = True,
    ):
        self.hypergraph = hypergraph
        self.audit_logger = audit_logger
        self.cache = cache_manager or IBGECacheManager()
        self.r_bridge = r_analyzer
        self.use_frailty = use_frailty
        self.generate_plots = generate_plots
        self.validator = SociologyBEAVERRules()
        self.visualizer = CanonicalVisualizer()
        self.expanded_models = ExpandedSociologyModels()

    def validate_policy_diffusion(
        self,
        policy_name: str,
        covariates: List[str],
        data_source: str = "IBGE",
        cluster_var: Optional[str] = None,  # Para frailty
        use_r: bool = True,  # Usar R se disponível
        generate_visualizations: bool = True,
        **kwargs
    ) -> CoxModelReport:
        # 1. Carregar dados COM CACHE
        df = self._load_data_with_cache(policy_name, data_source, **kwargs)

        # 2. Preparar dados
        df_clean = self._prepare_data(df, covariates)

        # 3. Escolher modelo: frailty se cluster especificado
        if self.use_frailty and cluster_var and cluster_var in df_clean.columns:
            if use_r and self.r_bridge:
                # Usar R para frailty real
                r_results = self.r_bridge.fit_cox(
                    df_clean, "tempo", "status", covariates, cluster=cluster_var
                )
                results = self._r_results_to_validation(r_results)
            else:
                # Fallback Python
                frailty_model = FrailtyCoxModel(frailty_type="gamma")
                frailty_result = frailty_model.fit(
                    df_clean, "tempo", "status", covariates, cluster_col=cluster_var
                )
                results = self._frailty_to_validation(frailty_result)
        else:
            # Cox padrão
            results = self._standard_cox_validation(df_clean, covariates)

        # 4. Gerar visualizações canônicas se solicitado
        visualizations = []
        if generate_visualizations:
            if 'km_data' in results:
                km_plot = self.visualizer.kaplan_meier(
                    df_clean, "tempo", "status",
                    group_var=covariates[0] if covariates else None,
                    title=f"Sobrevivência até Adoção: {policy_name}"
                )
                visualizations.append(km_plot)

            if 'cox_results' in results:
                forest_plot = self.visualizer.hazard_ratio_forest(
                    results['cox_results'],
                    title=f"Hazard Ratios: {policy_name}"
                )
                visualizations.append(forest_plot)

            if 'ph_test' in results:
                schoenfeld_plot = self.visualizer.schoenfeld_residuals(
                    results['ph_test'],
                    title=f"Teste de Proporcionalidade: {policy_name}"
                )
                visualizations.append(schoenfeld_plot)

        # 5. Construir relatório com visualizações
        report = CoxModelReport(
            dataset_name=policy_name,
            n_observations=len(df_clean),
            n_events=int(df_clean["status"].sum()),
            n_censored=int((df_clean["status"] == 0).sum()),
            covariates=covariates,
            results=results,
            overall_valid=self._assess_overall_validity(results),
            canonical_seal=self._generate_canonical_seal(results, df_clean),
            timestamp=time.time(),
            data_source=data_source,
            visualizations=[v.to_json() for v in visualizations],  # Novo campo
            cache_stats=self.cache.get_stats(),  # Novo campo
        )

        return report

    def _load_data_with_cache(self, policy_name, data_source, **kwargs):
        # Stub implementation
        import pandas as pd
        return pd.DataFrame({"tempo": [10, 20], "status": [1, 0]})

    def _prepare_data(self, df, covariates):
        # Stub implementation
        return df

    def _r_results_to_validation(self, r_results):
        # Stub implementation
        return r_results

    def _frailty_to_validation(self, frailty_result):
        # Stub implementation
        return frailty_result.to_dict()

    def _standard_cox_validation(self, df_clean, covariates):
        # Stub implementation
        return {}

    def _assess_overall_validity(self, results):
        # Stub implementation
        return True

    def _generate_canonical_seal(self, results, df_clean):
        # Stub implementation
        import hashlib
        return hashlib.sha256(b"stub").hexdigest()

    @staticmethod
    def validate_model(p_value: float, max_vif: float, is_linear: bool, is_independent: bool, is_homogeneous: bool = True, is_time_independent: bool = True) -> Dict[str, Any]:
        """
        Valida todas as suposições chave do modelo de Cox.
        Retorna um dicionário com os resultados de cada teste.
        """
        results = {
            "proportional_hazards": SociologyBEAVERRules._check_proportional_hazards(p_value),
            "multicollinearity": SociologyBEAVERRules._check_multicollinearity(max_vif),
            "linearity": SociologyBEAVERRules._check_linearity(is_linear),
            "independence": SociologyBEAVERRules._check_independence(is_independent),
            "homogeneous_distribution": SociologyBEAVERRules._check_homogeneous_distribution(is_homogeneous),
            "time_independence": SociologyBEAVERRules._check_time_independence(is_time_independent),
        }

        all_passed = all(res[0] for res in results.values())
        return {
            "is_valid": all_passed,
            "details": results
        }
