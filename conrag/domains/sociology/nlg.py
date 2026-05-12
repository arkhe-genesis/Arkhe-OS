#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/nlg.py — Natural Language Generation para Resultados Estatísticos
Traduz resultados técnicos de modelos de sobrevivência para linguagem natural
compreensível por stakeholders não-técnicos.

Características:
- Templates adaptativos por domínio (políticas públicas, saúde, educação)
- Explicações de Hazard Ratios em linguagem cotidiana
- Destaque para descobertas estatisticamente significativas
- Geração de resumos executivos com recomendações acionáveis
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

@dataclass
class NLGConfig:
    """Configuração para geração de linguagem natural."""
    audience: str = 'policy_maker'  # 'policy_maker', 'researcher', 'public', 'executive'
    language: str = 'pt-BR'
    include_uncertainty: bool = True  # Incluir intervalos de confiança nas explicações
    highlight_significant: bool = True  # Destacar efeitos significativos
    max_summary_length: int = 500  # Limite de caracteres para resumo executivo
    domain_context: str = 'public_policy'  # Contexto para adaptar linguagem

class ResultsNLG:
    """
    Gerador de linguagem natural para resultados estatísticos.

    Traduz:
    - Coeficientes de Cox → "Municípios com X têm Y% mais chance de adotar a política"
    - C-index → "O modelo consegue discriminar bem entre adoção rápida e lenta"
    - Pressupostos violados → "Atenção: o efeito de X pode variar ao longo do tempo"
    """

    # Templates por tipo de explicação
    TEMPLATES = {
        'hr_interpretation': {
            'gt_1': "{covariate} está associado a um aumento de {pct_change:.0f}% na taxa de adoção da política. Municípios com valores mais altos de {covariate} tendem a adotar mais rapidamente.",
            'lt_1': "{covariate} está associado a uma redução de {pct_change:.0f}% na taxa de adoção. Municípios com valores mais altos de {covariate} tendem a adotar mais lentamente.",
            'neutral': "{covariate} não apresenta efeito estatisticamente significativo na taxa de adoção da política.",
        },
        'c_index_interpretation': {
            'excellent': "O modelo apresenta excelente capacidade discriminatória (C-index = {c_index:.3f}), conseguindo distinguir claramente entre municípios que adotam rapidamente e os que adotam lentamente.",
            'good': "O modelo apresenta boa capacidade discriminatória (C-index = {c_index:.3f}), com desempenho acima do acaso na previsão da ordem de adoção.",
            'fair': "O modelo apresenta capacidade discriminatória moderada (C-index = {c_index:.3f}). Recomenda-se revisar covariáveis ou considerar interações.",
            'poor': "O modelo apresenta baixa capacidade discriminatória (C-index = {c_index:.3f}). Os resultados devem ser interpretados com cautela.",
        },
        'assumption_violation': {
            'proportional_hazards': "⚠️ O pressuposto de riscos proporcionais foi violado para {covariate}. Isso significa que o efeito de {covariate} na adoção pode variar ao longo do tempo. Considere incluir uma interação com o tempo ou estratificar por {covariate}.",
            'linearity': "⚠️ A relação entre {covariate} e o log-hazard pode não ser linear. Considere transformar {covariate} (ex: log, sqrt) ou usar splines.",
            'multicollinearity': "⚠️ Alta correlação entre covariáveis detectada (VIF > 5). Isso pode inflar erros-padrão. Considere remover uma das covariáveis correlacionadas ou usar PCA.",
        },
        'executive_summary': {
            'positive': "A análise indica que {key_finding}. Recomenda-se {recommendation} para acelerar a difusão da política.",
            'caution': "A análise apresenta evidências mistas. Embora {positive_aspect}, {caution_aspect}. Recomenda-se {recommendation}.",
            'negative': "A análise não encontrou evidências robustas de que as covariáveis analisadas influenciam a adoção da política. Sugere-se {recommendation}.",
        },
    }

    def __init__(self, config: Optional[NLGConfig] = None):
        self.config = config or NLGConfig()

    def explain_hazard_ratio(
        self,
        covariate: str,
        hr: float,
        ci_low: float,
        ci_high: float,
        p_value: float,
        alpha: float = 0.05,
    ) -> str:
        """
        Explica um Hazard Ratio em linguagem natural.

        Args:
            covariate: Nome da covariável
            hr: Hazard Ratio estimado
            ci_low, ci_high: Limites do IC 95%
            p_value: Valor-p do teste
            alpha: Nível de significância

        Returns:
            String com explicação em linguagem natural
        """
        # Verificar significância
        significant = p_value < alpha

        if not significant:
            return self.TEMPLATES['hr_interpretation']['neutral'].format(
                covariate=self._format_covariate_name(covariate)
            )

        # Calcular mudança percentual
        pct_change = (hr - 1) * 100

        if hr > 1:
            template = self.TEMPLATES['hr_interpretation']['gt_1']
        else:
            template = self.TEMPLATES['hr_interpretation']['lt_1']
            pct_change = abs(pct_change)  # Para frase "redução de X%"

        explanation = template.format(
            covariate=self._format_covariate_name(covariate),
            pct_change=pct_change,
        )

        # Adicionar incerteza se configurado
        if self.config.include_uncertainty:
            explanation += f" (IC 95%: {ci_low:.2f}–{ci_high:.2f})"

        return explanation

    def explain_c_index(self, c_index: float) -> str:
        """Explica o C-index (concordância) em linguagem natural."""
        if c_index >= 0.8:
            return self.TEMPLATES['c_index_interpretation']['excellent'].format(c_index=c_index)
        elif c_index >= 0.7:
            return self.TEMPLATES['c_index_interpretation']['good'].format(c_index=c_index)
        elif c_index >= 0.6:
            return self.TEMPLATES['c_index_interpretation']['fair'].format(c_index=c_index)
        else:
            return self.TEMPLATES['c_index_interpretation']['poor'].format(c_index=c_index)

    def explain_assumption_violation(
        self,
        assumption: str,
        covariate: Optional[str] = None,
        details: Optional[str] = None,
    ) -> str:
        """Explica violação de pressuposto em linguagem natural."""
        if assumption == 'proportional_hazards' and covariate:
            return self.TEMPLATES['assumption_violation']['proportional_hazards'].format(
                covariate=self._format_covariate_name(covariate)
            )
        elif assumption == 'linearity' and covariate:
            return self.TEMPLATES['assumption_violation']['linearity'].format(
                covariate=self._format_covariate_name(covariate)
            )
        elif assumption == 'multicollinearity':
            return self.TEMPLATES['assumption_violation']['multicollinearity']
        else:
            return f"⚠️ Pressuposto '{assumption}' violado: {details or 'Verifique a especificação do modelo.'}"

    def generate_executive_summary(
        self,
        cox_results: Dict,
        c_index: float,
        assumptions: Dict,
        key_findings: List[str],
    ) -> str:
        """
        Gera resumo executivo para tomadores de decisão.

        Args:
            cox_results: Dicionário com coeficientes do modelo
            c_index: C-index do modelo
            assumptions: Dict com resultados da validação de pressupostos
            key_findings: Lista de descobertas principais

        Returns:
            Resumo executivo em linguagem natural
        """
        # Identificar descobertas chave
        significant_effects = [
            (var, vals['hr'], vals['p'])
            for var, vals in cox_results.get('fixed_effects', {}).items()
            if vals.get('p', 1) < 0.05 and vals.get('hr')
        ]

        if not significant_effects:
            # Nenhum efeito significativo
            return self.TEMPLATES['executive_summary']['negative'].format(
                key_finding="nenhum fator analisado mostrou influência estatisticamente significativa",
                recommendation="ampliar o conjunto de covariáveis ou considerar interações não-lineares",
            )

        # Encontrar efeito mais forte
        strongest = max(significant_effects, key=lambda x: abs(np.log(x[1])))
        covariate, hr, p = strongest

        if hr > 1:
            direction = "acelera"
            action = "priorizar municípios com altos valores"
        else:
            direction = "retarda"
            action = "investigar barreiras em municípios com altos valores"

        positive_aspect = f"{self._format_covariate_name(covariate)} {direction} a adoção"

        # Verificar violações de pressupostos
        violations = [
            (name, result)
            for name, result in assumptions.items()
            if not getattr(result, 'passed', result.get('passed', True)) and getattr(result, 'severity', result.get('severity')) in ['error', 'warning']
        ]

        if violations:
            caution_aspect = f"o pressuposto de {violations[0][0]} requer atenção"
            recommendation = "reavaliar o modelo considerando a violação identificada"
            template = self.TEMPLATES['executive_summary']['caution']
        else:
            recommendation = f"{action} de {self._format_covariate_name(covariate)}"
            template = self.TEMPLATES['executive_summary']['positive']

        return template.format(
            key_finding=positive_aspect,
            positive_aspect=positive_aspect,
            caution_aspect=caution_aspect if 'caution_aspect' in locals() else "",
            recommendation=recommendation,
        )

    def explain_full_report(
        self,
        report: Any,  # Any used to avoid circular import dynamically
    ) -> Dict[str, str]:
        """
        Gera explicações completas para um relatório de análise.

        Returns:
            Dict com explicações por seção
        """
        explanations = {}

        # Explicar coeficientes
        if 'cox_results' in report.results:
            coefs = report.results['cox_results'].get('fixed_effects', {})
            coef_explanations = []
            for var, vals in coefs.items():
                if vals.get('hr'):
                    explanation = self.explain_hazard_ratio(
                        covariate=var,
                        hr=vals['hr'],
                        ci_low=vals.get('ci_low', vals['hr']),
                        ci_high=vals.get('ci_high', vals['hr']),
                        p_value=vals.get('p', 1),
                    )
                    coef_explanations.append(f"• {explanation}")
            explanations['coef_interpretations'] = "\n".join(coef_explanations)

        # Explicar C-index
        c_index = report.results.get('concordance', 0.5) if isinstance(report.results, dict) else 0.5
        explanations['model_discrimination'] = self.explain_c_index(c_index)

        # Explicar pressupostos
        assumption_explanations = []
        for assumption, result in report.results.items():
            passed = getattr(result, 'passed', result.get('passed', True) if isinstance(result, dict) else True)
            if not passed:
                explanation = self.explain_assumption_violation(
                    assumption=assumption,
                    covariate=getattr(result, 'covariate', result.get('covariate') if isinstance(result, dict) else None),
                    details=getattr(result, 'message', result.get('message') if isinstance(result, dict) else None),
                )
                assumption_explanations.append(explanation)
        if assumption_explanations:
            explanations['assumption_warnings'] = "\n\n".join(assumption_explanations)

        # Resumo executivo
        explanations['executive_summary'] = self.generate_executive_summary(
            cox_results=report.results.get('cox_results', {}) if isinstance(report.results, dict) else {},
            c_index=c_index,
            assumptions=report.results,
            key_findings=[],  # Pode ser populado com análise adicional
        )

        return explanations

    def _format_covariate_name(self, name: str) -> str:
        """Formata nome de covariável para linguagem natural."""
        # Mapeamento de nomes técnicos para linguagem natural
        mappings = {
            'pib_per_capita': 'PIB per capita',
            'populacao': 'população',
            'regiao': 'região',
            'idh': 'Índice de Desenvolvimento Humano (IDH)',
            'governanca': 'índice de governança',
            'educacao': 'nível educacional',
        }
        return mappings.get(name, name.replace('_', ' ').title())

    def to_markdown(self, explanations: Dict[str, str]) -> str:
        """Converte explicações para formato Markdown."""
        md = []

        if 'executive_summary' in explanations:
            md.append(f"## 📋 Resumo Executivo\n\n{explanations['executive_summary']}\n")

        if 'model_discrimination' in explanations:
            md.append(f"## 📊 Capacidade Discriminatória do Modelo\n\n{explanations['model_discrimination']}\n")

        if 'coef_interpretations' in explanations:
            md.append(f"## 🔍 Interpretação dos Efeitos\n\n{explanations['coef_interpretations']}\n")

        if 'assumption_warnings' in explanations:
            md.append(f"## ⚠️ Alertas sobre Pressupostos\n\n{explanations['assumption_warnings']}\n")

        return "\n".join(md)
