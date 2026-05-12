#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/pdf_report.py — Gerador de Relatórios PDF Canônicos
Gera relatórios PDF auditáveis com:
- Plots canônicos (Kaplan-Meier, forest, Schoenfeld)
- Tabelas de coeficientes formatadas
- Selos canônicos SHA3-256 para integridade
- Metadados de auditoria (timestamp, versão, hash)

Dependências:
- weasyprint ou reportlab para geração PDF
- plotly ou matplotlib para plots
- pandas para formatação de tabelas
"""

import json
import hashlib
import time
import base64
import io
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd

try:
    from weasyprint import HTML, CSS
    WEAASYPRINT_AVAILABLE = True
except ImportError:
    WEAASYPRINT_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

@dataclass
class PDFReportConfig:
    """Configuração para geração de relatório PDF."""
    title: str
    subtitle: Optional[str] = None
    author: str = "ARKHE Cathedral — Sociology Domain"
    policy_name: Optional[str] = None
    include_plots: bool = True
    include_tables: bool = True
    include_canonical_seal: bool = True
    page_size: str = "A4"
    language: str = "pt-BR"
    theme: str = "canonical"  # "canonical", "minimal", "dark"

class CanonicalPDFReport:
    """Gera relatório PDF canônico a partir de resultados de análise."""

    # Templates HTML canônicos
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="{language}">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @page {{ size: {page_size}; margin: 2cm; }}
            body {{ font-family: "Helvetica", "Arial", sans-serif; line-height: 1.6; color: #333; }}
            .header {{ text-align: center; border-bottom: 3px solid #1f77b4; padding-bottom: 1em; margin-bottom: 2em; }}
            .title {{ font-size: 24pt; font-weight: bold; color: #1f77b4; }}
            .subtitle {{ font-size: 14pt; color: #666; margin-top: 0.5em; }}
            .meta {{ font-size: 10pt; color: #999; margin-top: 1em; }}
            .section {{ margin: 2em 0; }}
            .section-title {{ font-size: 16pt; font-weight: bold; color: #1f77b4; border-left: 4px solid #1f77b4; padding-left: 0.5em; }}
            table {{ width: 100%; border-collapse: collapse; margin: 1em 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .plot-container {{ text-align: center; margin: 2em 0; }}
            .canonical-seal {{ font-family: monospace; font-size: 9pt; color: #666; background: #f9f9f9; padding: 1em; border: 1px dashed #ccc; margin-top: 3em; }}
            .footer {{ text-align: center; font-size: 9pt; color: #999; margin-top: 3em; border-top: 1px solid #eee; padding-top: 1em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{title}</div>
            {subtitle_block}
            <div class="meta">
                Gerado por ARKHE OS • Sociology Domain • {timestamp}<br>
                Política: {policy_name} • Domínio: {domain}
            </div>
        </div>

        {content}

        {canonical_seal_block}

        <div class="footer">
            Documento canônico ARKHE • Hash de integridade: {canonical_hash}<br>
            Verificável em: https://arkhe-os.github.io/verify/{canonical_hash}
        </div>
    </body>
    </html>
    """

    def __init__(self, config: PDFReportConfig):
        self.config = config
        self.plots: List[Dict] = []
        self.tables: List[Dict] = []
        self.sections: List[Dict] = []
        self.canonical_hash: Optional[str] = None

    def add_plot(self, plot_data: Dict, title: str, caption: str):
        """Adiciona plot ao relatório."""
        self.plots.append({
            'data': plot_data,
            'title': title,
            'caption': caption,
        })

    def add_table(self, df: pd.DataFrame, title: str, caption: str, format_fn=None):
        """Adiciona tabela ao relatório."""
        if format_fn:
            df = format_fn(df)
        self.tables.append({
            'dataframe': df,
            'title': title,
            'caption': caption,
            'html': df.to_html(index=False, classes='data-table', border=0),
        })

    def add_section(self, title: str, content: str):
        """Adiciona seção de texto ao relatório."""
        self.sections.append({'title': title, 'content': content})

    def _render_plot_html(self, plot: Dict) -> str:
        """Renderiza plot como HTML (base64 PNG ou Plotly)."""
        if not PLOTLY_AVAILABLE:
            return f"<p><em>[Plot: {plot['title']}]</em></p>"

        # Converter dados canônicos para Plotly
        if plot['data'].get('plot_type') == 'kaplan_meier':
            fig = self._km_to_plotly(plot['data'])
        elif plot['data'].get('plot_type') == 'forest':
            fig = self._forest_to_plotly(plot['data'])
        else:
            fig = go.Figure()
            fig.add_annotation(text=f"Plot: {plot['title']}", showarrow=False)

        # Converter para PNG base64 para WeasyPrint
        img_bytes = pio.to_image(fig, format='png', width=800, height=600)
        img_base64 = base64.b64encode(img_bytes).decode()

        return f"""
        <div class="plot-container">
            <p><strong>{plot['title']}</strong></p>
            <img src="data:image/png;base64,{img_base64}" alt="{plot['title']}" style="max-width:100%; height:auto;">
            <p style="font-size:10pt; color:#666; font-style:italic;">{plot['caption']}</p>
        </div>
        """

    def _km_to_plotly(self, km_data: Dict) -> go.Figure:
        """Converte dados Kaplan-Meier canônicos para Plotly."""
        fig = go.Figure()
        for curve in km_data.get('curves', []):
            fig.add_trace(go.Scatter(
                x=curve['times'],
                y=curve['survival'],
                mode='lines',
                name=curve['group'],
                fill='tozeroy',
                opacity=0.7,
            ))
        fig.update_layout(
            title='Kaplan-Meier Survival Estimate',
            xaxis_title='Tempo',
            yaxis_title='Probabilidade de Sobrevivência',
            hovermode='x unified',
        )
        return fig

    def _forest_to_plotly(self, forest_data: Dict) -> go.Figure:
        """Converte dados de forest plot para Plotly."""
        effects = forest_data.get('effects', [])
        y_labels = [e['variable'] for e in effects]
        x_values = [e['hr'] for e in effects]
        x_lower = [e['ci_low'] for e in effects]
        x_upper = [e['ci_high'] for e in effects]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_lower + x_upper[::-1],
            y=y_labels + y_labels[::-1],
            fill='toself',
            fillcolor='rgba(0,100,80,0.2)',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            name='95% CI',
        ))
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_labels,
            mode='markers',
            marker=dict(size=8, color='#1f77b4'),
            name='Hazard Ratio',
        ))
        fig.add_vline(x=1.0, line_dash='dash', line_color='red', annotation_text='HR=1.0')
        fig.update_layout(
            title='Forest Plot — Hazard Ratios',
            xaxis_title='Hazard Ratio (log scale)',
            yaxis_title='Covariável',
            xaxis_type='log',
            hovermode='y unified',
        )
        return fig

    def _generate_canonical_seal(self, content: str) -> str:
        """Gera selo canônico SHA3-256 do conteúdo."""
        return hashlib.sha3_256(content.encode()).hexdigest()

    def generate(self, output_path: Union[str, Path]) -> str:
        """Gera arquivo PDF e retorna caminho."""
        if not WEAASYPRINT_AVAILABLE:
            raise ImportError("weasyprint required for PDF generation")

        # Montar conteúdo HTML
        subtitle_block = f'<div class="subtitle">{self.config.subtitle}</div>' if self.config.subtitle else ''

        sections_html = ''.join([
            f"""
            <div class="section">
                <div class="section-title">{s['title']}</div>
                <p>{s['content']}</p>
            </div>
            """ for s in self.sections
        ])

        plots_html = ''.join([f'<div class="section">{self._render_plot_html(p)}</div>' for p in self.plots]) if self.config.include_plots else ''

        tables_html = ''.join([
            f"""
            <div class="section">
                <div class="section-title">{t['title']}</div>
                <p style="font-size:10pt; color:#666; font-style:italic;">{t['caption']}</p>
                {t['html']}
            </div>
            """ for t in self.tables
        ]) if self.config.include_tables else ''

        content = sections_html + plots_html + tables_html

        # Selo canônico
        seal_block = ''
        if self.config.include_canonical_seal:
            self.canonical_hash = self._generate_canonical_seal(content)
            seal_block = f"""
            <div class="canonical-seal">
                <strong>🔐 Selo Canônico de Integridade</strong><br>
                Hash SHA3-256: <code>{self.canonical_hash}</code><br>
                Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}<br>
                Versão: ARKHE OS Sociology Domain v2.1
            </div>
            """

        # Template final
        html_content = self.HTML_TEMPLATE.format(
            language=self.config.language,
            title=self.config.title,
            subtitle_block=subtitle_block,
            policy_name=self.config.policy_name or 'N/A',
            domain='Sociology',
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            page_size=self.config.page_size,
            content=content,
            canonical_seal_block=seal_block,
            canonical_hash=self.canonical_hash or 'pending',
        )

        # Gerar PDF
        html_doc = HTML(string=html_content)
        css = CSS(string='@page { size: A4; margin: 2cm; }')
        pdf_bytes = html_doc.write_pdf(stylesheets=[css])

        # Salvar arquivo
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        return str(output_path)
