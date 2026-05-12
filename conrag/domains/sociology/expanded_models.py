#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/expanded_models.py — Modelos Adicionais para Ciências Sociais
Expande o domínio Sociology para além do Cox, cobrindo:
- Logistic regression (desfechos binários)
- Multilevel/hierarchical models (dados aninhados)
- Structural Equation Modeling (SEM) para mediação/moderação
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False

@dataclass
class LogisticRegressionResult:
    """Resultado de regressão logística."""
    dependent_var: str
    independent_vars: List[str]
    coefficients: Dict[str, Dict]  # {var: {coef, se, p, or, ci_low, ci_high}}
    pseudo_r2: Dict[str, float]  # McFadden, Cox-Snell, Nagelkerke
    aic: float
    bic: float
    confusion_matrix: Dict  # Se thresholds especificados
    warnings: List[str]

@dataclass
class MultilevelResult:
    """Resultado de modelo multinível."""
    model_type: str  # "lmer", "glmer", "mixedlm"
    fixed_effects: Dict[str, Dict]
    random_effects: Dict[str, Dict]  # {group: {variance, sd}}
    icc: float  # Intraclass Correlation Coefficient
    aic: float
    bic: float
    warnings: List[str]

class ExpandedSociologyModels:
    """Modelos estatísticos expandidos para domínio Sociology."""

    @staticmethod
    def logistic_regression(
        df: pd.DataFrame,
        outcome: str,
        predictors: List[str],
        weights: Optional[str] = None,
        interaction_terms: Optional[List[str]] = None,
    ) -> LogisticRegressionResult:
        """Ajusta regressão logística."""
        if not STATS_AVAILABLE:
            raise RuntimeError("statsmodels required for logistic regression")

        # Preparar fórmula
        formula = f"{outcome} ~ {' + '.join(predictors)}"
        if interaction_terms:
            formula += " + " + " + ".join(interaction_terms)

        # Ajustar modelo
        model = smf.logit(formula=formula, data=df)
        if weights and weights in df.columns:
            result = model.fit(method='bfgs', disp=False, freq_weights=df[weights])
        else:
            result = model.fit(method='bfgs', disp=False)

        # Extrair coeficientes
        coefficients = {}
        for var in predictors + (interaction_terms or []):
            if var in result.params:
                coef = result.params[var]
                se = result.bse[var]
                p = result.pvalues[var]
                or_val = np.exp(coef)  # Odds ratio
                ci_low = np.exp(coef - 1.96 * se)
                ci_high = np.exp(coef + 1.96 * se)
                coefficients[var] = {
                    'coef': float(coef), 'se': float(se), 'p': float(p),
                    'odds_ratio': float(or_val), 'ci_low': float(ci_low), 'ci_high': float(ci_high),
                }

        # Pseudo-R²
        pr2 = {
            'mcfadden': 1 - (result.llf / result.llnull),
            'cox_snell': 1 - np.exp((result.llnull - result.llf) * 2 / len(df)),
        }
        pr2['nagelkerke'] = pr2['cox_snell'] / (1 - np.exp(result.llnull * 2 / len(df)))

        return LogisticRegressionResult(
            dependent_var=outcome,
            independent_vars=predictors,
            coefficients=coefficients,
            pseudo_r2={k: float(v) for k, v in pr2.items()},
            aic=float(result.aic),
            bic=float(result.bic),
            confusion_matrix={},  # Preencher se thresholds fornecidos
            warnings=[str(w) for w in result.warnings] if hasattr(result, 'warnings') else [],
        )

    @staticmethod
    def multilevel_model(
        df: pd.DataFrame,
        outcome: str,
        fixed_effects: List[str],
        random_effects: Dict[str, List[str]],  # {group_var: [random_vars]}
        family: str = "gaussian",  # "gaussian", "binomial", "poisson"
    ) -> MultilevelResult:
        """Ajusta modelo multinível (mixed effects)."""
        if not STATS_AVAILABLE:
            raise RuntimeError("statsmodels required for multilevel models")

        warnings_list = []

        # Construir fórmula
        fe_formula = ' + '.join(fixed_effects)

        # Random effects: (1 | group) ou (var | group)
        re_formulas = []
        for group_var, rand_vars in random_effects.items():
            if rand_vars:
                re_formulas.append(f"({' + '.join(rand_vars)} | {group_var})")
            else:
                re_formulas.append(f"(1 | {group_var})")

        full_formula = f"{outcome} ~ {fe_formula} + {' + '.join(re_formulas)}"

        try:
            if not random_effects:
                raise ValueError("At least one random effect group must be specified")
            group_key = list(random_effects.keys())[0]
            if family == "gaussian":
                model = smf.mixedlm(full_formula, df, groups=df[group_key])
            else:
                # Para GLMM: usar pymer4 ou R via reticulate
                warnings_list.append(f"Family '{family}' requires R/reticulate — using Gaussian approximation")
                model = smf.mixedlm(full_formula, df, groups=df[group_key])

            result = model.fit(reml=False, disp=False)

            # Fixed effects
            fixed_results = {}
            for var in fixed_effects:
                if var in result.fe_params:
                    fixed_results[var] = {
                        'coef': float(result.fe_params[var]),
                        'se': float(result.bse[var]),
                        'p': float(result.pvalues[var]),
                    }

            # Random effects variance
            random_results = {}
            for group_var in random_effects.keys():
                if hasattr(result, 'cov_re') and result.cov_re is not None:
                    random_results[group_var] = {
                        'variance': float(np.diag(result.cov_re).sum()),
                        'sd': float(np.sqrt(np.diag(result.cov_re).sum())),
                    }

            # ICC (para random intercept only)
            if len(random_effects) == 1 and not random_effects[list(random_effects.keys())[0]]:
                group_var = list(random_effects.keys())[0]
                re_var = random_results.get(group_var, {}).get('variance', 0)
                resid_var = result.scale if hasattr(result, 'scale') else 1
                icc = re_var / (re_var + resid_var) if (re_var + resid_var) > 0 else 0
            else:
                icc = None

            return MultilevelResult(
                model_type="mixedlm",
                fixed_effects=fixed_results,
                random_effects=random_results,
                icc=float(icc) if icc is not None else None,
                aic=float(result.aic),
                bic=float(result.bic),
                warnings=warnings_list,
            )

        except Exception as e:
            warnings_list.append(f"Model fitting warning: {str(e)}")
            return MultilevelResult(
                model_type="failed",
                fixed_effects={},
                random_effects={},
                icc=None,
                aic=float('inf'),
                bic=float('inf'),
                warnings=warnings_list,
            )

    @staticmethod
    def sem_path_analysis(
        df: pd.DataFrame,
        model_spec: Dict,
        # model_spec = {
        #   'regressions': {'Y ~ X1 + X2': 'direct'},
        #   'mediations': {'X1 -> M -> Y': 'indirect'},
        #   'covariances': ['X1 ~~ X2'],
        # }
    ) -> Dict:
        """
        Análise de caminhos via SEM.

        Nota: Implementação completa requer `semopy` ou R/lavaan.
        Esta é uma interface canônica — em produção, delegar para R.
        """
        # Placeholder: retornar estrutura canônica
        return {
            'model_spec': model_spec,
            'fit_indices': {
                'chi2': None, 'df': None, 'p': None,
                'cfi': None, 'tli': None, 'rmsea': None, 'srmr': None,
            },
            'path_coefficients': {},
            'indirect_effects': {},
            'warnings': ['SEM requires semopy or R/lavaan — using placeholder'],
        }
