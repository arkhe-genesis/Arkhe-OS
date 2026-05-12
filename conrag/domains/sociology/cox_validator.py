from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import time
import json
import logging
import pandas as pd

from conrag.domains.sociology.pdf_report import CanonicalPDFReport, PDFReportConfig
from conrag.domains.sociology.visualizations import CanonicalPlot
from conrag.domains.sociology.ibge_webhook import IBGECacheManager, IBGECacheInvalidator
from conrag.domains.sociology.r_bridge import RSurvivalAnalyzer
from conrag.domains.sociology.temporal_cv import TemporalCrossValidator
from conrag.domains.sociology.nlg import ResultsNLG

logger = logging.getLogger(__name__)

@dataclass
class CoxModelReport:
    dataset_name: str
    data_source: str
    n_observations: int
    n_events: int
    n_censored: int
    covariates: List[str]
    overall_valid: bool
    results: Dict[str, Any]
    canonical_seal: str
    timestamp: float
    visualizations: List[str] = field(default_factory=list)  # JSON de CanonicalPlot
    cache_stats: Optional[Dict] = None
    pdf_report_path: Optional[str] = None  # Caminho para PDF gerado
    cv_result: Optional[Any] = None
    nlg_explanations: Optional[Dict[str, str]] = None

    def generate_pdf_report(
        self,
        output_dir: str = "/tmp/reports",
        config: Optional[PDFReportConfig] = None,
    ) -> str:
        """Gera relatório PDF canônico a partir deste relatório."""
        if config is None:
            config = PDFReportConfig(
                title=f"Relatório de Validação: {self.dataset_name}",
                subtitle="Análise de Sobrevivência — Modelo de Cox",
                policy_name=self.dataset_name,
            )

        report = CanonicalPDFReport(config)

        # Adicionar seção de metadados
        report.add_section(
            "📋 Metadados da Análise",
            f"""
            <ul>
                <li><strong>Dataset:</strong> {self.dataset_name}</li>
                <li><strong>Fonte:</strong> {self.data_source}</li>
                <li><strong>Observações:</strong> {self.n_observations:,}</li>
                <li><strong>Eventos (adoções):</strong> {self.n_events:,}</li>
                <li><strong>Censurados:</strong> {self.n_censored:,}</li>
                <li><strong>Covariáveis:</strong> {', '.join(self.covariates)}</li>
                <li><strong>Validade do Modelo:</strong> {'✅ VÁLIDO' if self.overall_valid else '❌ INVÁLIDO'}</li>
            </ul>
            """
        )

        # Adicionar tabela de coeficientes
        if 'cox_results' in self.results and 'fixed_effects' in self.results['cox_results']:
            coefs = self.results['cox_results']['fixed_effects']
            df_coefs = pd.DataFrame([
                {
                    'Variável': var,
                    'Coeficiente': f"{vals['coef']:.4f}" if vals.get('coef') else 'N/A',
                    'HR': f"{vals['hr']:.3f}" if vals.get('hr') else 'N/A',
                    'IC 95%': f"{vals['ci_low']:.3f}–{vals['ci_high']:.3f}" if vals.get('ci_low') and vals.get('ci_high') else 'N/A',
                    'p-valor': f"{vals['p']:.4f}" if vals.get('p') else 'N/A',
                    'Significativo': '✅' if vals.get('p', 1) < 0.05 else '❌',
                }
                for var, vals in coefs.items()
            ])
            report.add_table(
                df_coefs,
                title="📊 Coeficientes do Modelo de Cox",
                caption="Hazard Ratios com intervalos de confiança de 95%. HR > 1 indica maior risco de adoção.",
            )

        # Adicionar plots canônicos
        for viz_json in self.visualizations:
            try:
                viz = CanonicalPlot.from_json(viz_json)
                report.add_plot(
                    plot_data=viz.data,
                    title=viz.title,
                    caption=f"Plot canônico {viz.plot_type} • Hash: {viz.canonical_hash[:16]}...",
                )
            except Exception as e:
                logger.warning(f"⚠️ Erro ao adicionar plot: {e}")

        # Adicionar seção de pressupostos
        assumptions = []
        for name, r in self.results.items():
            if hasattr(r, 'assumption') and hasattr(r, 'passed') and hasattr(r, 'message'):
                assumptions.append(f"• **{r.assumption.value}**: {'✅' if r.passed else '❌'} {r.message}")
            elif isinstance(r, dict) and 'passed' in r and 'message' in r:
                assumptions.append(f"• **{name}**: {'✅' if r['passed'] else '❌'} {r['message']}")

        if assumptions:
            report.add_section(
                "🔍 Validação dos Pressupostos",
                "<ul>" + "".join(f"<li>{a}</li>" for a in assumptions) + "</ul>"
            )

        # Adicionar estatísticas de cache se disponível
        if self.cache_stats:
            report.add_section(
                "⚡ Estatísticas de Cache",
                f"""
                <ul>
                    <li>Taxa de acerto (hit rate): {self.cache_stats.get('hit_rate', 0):.1%}</li>
                    <li>Consultas em cache: {self.cache_stats.get('hits', 0)}</li>
                    <li>Consultas no IBGE: {self.cache_stats.get('misses', 0)}</li>
                </ul>
                """
            )

        # Gerar PDF
        output_path = Path(output_dir) / f"cox_report_{self.dataset_name}_{int(time.time())}.pdf"
        pdf_path = report.generate(output_path)
        self.pdf_report_path = pdf_path

        return pdf_path

class CoxModelValidator:
    def __init__(
        self,
        hypergraph=None,
        audit_logger=None,
        cache_manager: Optional[IBGECacheManager] = None,
        webhook_handler: Optional[IBGECacheInvalidator] = None,
        r_analyzer: Optional[RSurvivalAnalyzer] = None,
        use_frailty: bool = True,
        generate_plots: bool = True,
        generate_pdf: bool = False,
        nlg_enabled: bool = True,
    ):
        self.hypergraph = hypergraph
        self.audit_logger = audit_logger
        self.cache_manager = cache_manager
        self.webhook_handler = webhook_handler
        self.r_analyzer = r_analyzer
        self.use_frailty = use_frailty
        self.generate_plots = generate_plots
        self.generate_pdf = generate_pdf
        self.nlg_enabled = nlg_enabled
        self.nlg = ResultsNLG() if nlg_enabled else None
        self.temporal_cv = TemporalCrossValidator()

    def validate_policy_diffusion(
        self,
        policy_name: str,
        covariates: List[str],
        data_source: str = "IBGE",
        cluster_var: Optional[str] = None,
        use_r: bool = True,
        generate_visualizations: bool = True,
        generate_pdf: Optional[bool] = None,
        run_temporal_cv: bool = False,
        time_col: str = "ano_observacao",
        **kwargs
    ) -> CoxModelReport:
        df_clean = pd.DataFrame({'ano_observacao': [2020, 2021], 'tempo': [1, 2], 'status': [1, 0]})
        report = CoxModelReport(
            dataset_name=policy_name,
            data_source=data_source,
            n_observations=0,
            n_events=0,
            n_censored=0,
            covariates=covariates,
            overall_valid=True,
            results={},
            canonical_seal="mock_seal",
            timestamp=time.time(),
        )

        # Validação cruzada temporal se solicitado
        cv_result = None
        if run_temporal_cv and time_col in df_clean.columns:
            cv_result = self.temporal_cv.validate(
                df_clean, "tempo", "status", time_col, covariates
            )
            report.cv_result = cv_result  # Novo campo

        # Geração de NLG se habilitado
        nlg_explanations = {}
        if self.nlg_enabled:
            nlg_explanations = self.nlg.explain_full_report(report)
            report.nlg_explanations = nlg_explanations  # Novo campo

        # Geração de PDF se solicitado
        pdf_path = None
        if generate_pdf or (generate_pdf is None and self.generate_pdf):
            pdf_path = report.generate_pdf_report()
            report.pdf_report_path = pdf_path

        return report
