"""Dashboard interativo para visualização de resultados de validação."""
import plotly.graph_objects as go
import plotly.express as px
from typing import List
import numpy as np

class ValidationDashboard:
    """Gera visualizações interativas para relatórios de validação."""

    @staticmethod
    def coherence_scatter(report: 'ValidationReport') -> go.Figure:
        """Gráfico de dispersão: predito vs. observado com barras de erro."""
        x_pred = [r.predicted_value for r in report.cve_results if not np.isnan(r.observed_value)]
        y_obs = [r.observed_value for r in report.cve_results if not np.isnan(r.observed_value)]
        x_err = [r.predicted_error for r in report.cve_results if not np.isnan(r.observed_value)]
        y_err = [r.observed_error for r in report.cve_results if not np.isnan(r.observed_value)]
        labels = [r.cve_id for r in report.cve_results if not np.isnan(r.observed_value)]
        colors = ['#2ecc71' if r.passed else '#e74c3c' for r in report.cve_results if not np.isnan(r.observed_value)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_pred, y=y_obs,
            error_x=dict(array=x_err, color='rgba(46,204,113,0.5)'),
            error_y=dict(array=y_err, color='rgba(46,204,113,0.5)'),
            mode='markers+text',
            marker=dict(size=12, color=colors, line=dict(width=2, color='white')),
            text=labels,
            textposition='top center',
            name='CVEs'
        ))

        # Linha de identidade (predito = observado)
        if x_pred and y_obs:
            min_val = min(min(x_pred), min(y_obs)) * 0.9
            max_val = max(max(x_pred), max(y_obs)) * 1.1
            fig.add_trace(go.Scatter(
                x=[min_val, max_val], y=[min_val, max_val],
                mode='lines', line=dict(dash='dash', color='gray'),
                name='Identidade (teoria = experimento)'
            ))

        fig.update_layout(
            title=f"Validação Substrato {report.substrate_id}: {report.experiment_type}",
            xaxis_title="Valor Predito (Ψ_ToE)",
            yaxis_title="Valor Observado (Experimento)",
            hovermode='closest',
            template='plotly_white',
            height=500
        )
        return fig

    @staticmethod
    def coherence_histogram(reports: List['ValidationReport']) -> go.Figure:
        """Histograma da distribuição de coerências globais."""
        coherences = [r.global_coherence for r in reports if r.global_coherence > 0]

        fig = px.histogram(
            x=coherences, nbins=20,
            title="Distribuição de Coerência Global Φ_C",
            labels={'x': 'Coerência Φ_C', 'y': 'Frequência'},
            color_discrete_sequence=['#3498db']
        )

        # Linhas de threshold
        fig.add_vline(x=0.8, line_dash='dash', line_color='orange', annotation_text='Threshold 0.8')
        fig.add_vline(x=0.9, line_dash='dash', line_color='green', annotation_text='Alta confiança')

        fig.update_layout(template='plotly_white', height=400)
        return fig

    @staticmethod
    def mercy_gap_analysis(report: 'ValidationReport') -> go.Figure:
        """Análise do mercy gap: diferença relativa por CVE."""
        cves = [r.cve_id for r in report.cve_results if not np.isnan(r.observed_value)]
        rel_deltas = [
            abs(r.observed_value - r.predicted_value) / abs(r.predicted_value) if r.predicted_value != 0 else 0
            for r in report.cve_results if not np.isnan(r.observed_value)
        ]
        colors = [
            '#2ecc71' if (0.04 <= d <= 0.10) else '#e74c3c' if d < 0.04 else '#f39c12'
            for d in rel_deltas
        ]

        fig = go.Figure(data=[
            go.Bar(
                x=cves, y=rel_deltas,
                marker_color=colors,
                text=[f"{d*100:.1f}%" for d in rel_deltas],
                textposition='auto'
            )
        ])

        fig.add_hrect(y0=0.04, y1=0.10, fillcolor="rgba(46,204,113,0.1)", layer='below')
        fig.update_layout(
            title="Análise de Mercy Gap δ ∈ [0.04, 0.10]",
            yaxis_title="Diferença Relativa |Δ|/|predito|",
            xaxis_title="CVE",
            template='plotly_white',
            height=400
        )
        return fig
