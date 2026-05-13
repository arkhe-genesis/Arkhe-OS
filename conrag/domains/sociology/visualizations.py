#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/sociology/visualizations.py — Visualizações Canônicas
Gera plots padronizados para análise de sobrevivência, compatíveis com
auditoria e reprodutibilidade.

Formatos de saída:
- PNG/SVG para relatórios
- JSON/Plotly para dashboards interativos
- ASCII para logs/terminal
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class CanonicalPlot:
    """Representação canônica de um plot para auditoria."""
    plot_type: str  # "kaplan_meier", "hazard_ratio", "forest", "schoenfeld"
    title: str
    data: Dict  # Dados estruturados para re-renderização
    metadata: Dict  # Configurações, cores, labels
    canonical_hash: str  # SHA3-256 dos dados + metadata
    generated_at: float

    def to_json(self) -> str:
        """Serializa para JSON canônico."""
        return json.dumps({
            'plot_type': self.plot_type,
            'title': self.title,
            'data': self.data,
            'metadata': self.metadata,
            'canonical_hash': self.canonical_hash,
            'generated_at': self.generated_at,
        }, sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> 'CanonicalPlot':
        """Deserializa de JSON canônico."""
        data = json.loads(json_str)
        return cls(**data)

class CanonicalVisualizer:
    """Gerador de visualizações canônicas."""

    # Paleta de cores canônica (acessível, daltônico)
    CANONICAL_COLORS = {
        'primary': '#1f77b4',    # Azul
        'secondary': '#ff7f0e',  # Laranja
        'success': '#2ca02c',    # Verde
        'warning': '#d62728',    # Vermelho
        'neutral': '#7f7f7f',    # Cinza
        'background': '#ffffff',
        'grid': '#e0e0e0',
    }

    @staticmethod
    def kaplan_meier(
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        group_var: Optional[str] = None,
        title: str = "Kaplan-Meier Survival Estimate",
        x_label: str = "Tempo",
        y_label: str = "Probabilidade de Sobrevivência",
    ) -> CanonicalPlot:
        """Gera dados para plot Kaplan-Meier canônico."""
        try:
            from lifelines import KaplanMeierFitter
        except ImportError:
            return CanonicalPlot('kaplan_meier', title, {}, {}, "", time.time())

        data = {'curves': []}

        if group_var and group_var in df.columns:
            # KM por grupo
            for group in df[group_var].unique():
                group_df = df[df[group_var] == group].copy()
                kmf = KaplanMeierFitter()
                kmf.fit(group_df[duration_col], event_observed=group_df[event_col], label=str(group))

                data['curves'].append({
                    'group': str(group),
                    'times': kmf.survival_function_.index.tolist(),
                    'survival': kmf.survival_function_[str(group)].tolist(),
                    'ci_lower': kmf.confidence_interval_['lower'].tolist(),
                    'ci_upper': kmf.confidence_interval_['upper'].tolist(),
                    'n_at_risk': kmf.at_risk_counts.tolist() if hasattr(kmf, 'at_risk_counts') else None,
                })
        else:
            # KM global
            kmf = KaplanMeierFitter()
            kmf.fit(df[duration_col], event_observed=df[event_col])
            data['curves'].append({
                'group': 'all',
                'times': kmf.survival_function_.index.tolist(),
                'survival': kmf.survival_function_.iloc[:, 0].tolist(),
                'ci_lower': kmf.confidence_interval_['lower'].tolist(),
                'ci_upper': kmf.confidence_interval_['upper'].tolist(),
            })

        metadata = {
            'x_label': x_label,
            'y_label': y_label,
            'colors': CanonicalVisualizer.CANONICAL_COLORS,
            'show_ci': True,
            'show_risk_table': True,
        }

        canonical_hash = hashlib.sha3_256(
            json.dumps({'data': data, 'metadata': metadata}, sort_keys=True).encode()
        ).hexdigest()

        return CanonicalPlot(
            plot_type='kaplan_meier',
            title=title,
            data=data,
            metadata=metadata,
            canonical_hash=canonical_hash,
            generated_at=time.time(),
        )

    @staticmethod
    def hazard_ratio_forest(
        cox_results: Dict,
        title: str = "Hazard Ratios — Cox Proportional Hazards Model",
        reference_line: float = 1.0,
    ) -> CanonicalPlot:
        """Gera forest plot de hazard ratios."""
        effects = []
        for var, stats in cox_results.get('fixed_effects', {}).items():
            effects.append({
                'variable': var,
                'hr': stats.get('hr'),
                'ci_low': stats.get('ci_low'),
                'ci_high': stats.get('ci_high'),
                'p_value': stats.get('p'),
                'significant': stats.get('p', 1) < 0.05,
            })

        # Ordenar por magnitude do efeito
        effects.sort(key=lambda x: abs(np.log(x['hr']) if x['hr'] else 0), reverse=True)

        data = {
            'effects': effects,
            'reference_line': reference_line,
            'x_scale': 'log',  # Hazard ratios em escala log
        }

        metadata = {
            'x_label': 'Hazard Ratio (95% CI)',
            'y_label': 'Covariável',
            'colors': {
                'significant': CanonicalVisualizer.CANONICAL_COLORS['success'],
                'non_significant': CanonicalVisualizer.CANONICAL_COLORS['neutral'],
                'reference': CanonicalVisualizer.CANONICAL_COLORS['warning'],
            },
        }

        canonical_hash = hashlib.sha3_256(
            json.dumps({'data': data, 'metadata': metadata}, sort_keys=True).encode()
        ).hexdigest()

        return CanonicalPlot(
            plot_type='forest',
            title=title,
            data=data,
            metadata=metadata,
            canonical_hash=canonical_hash,
            generated_at=time.time(),
        )

    @staticmethod
    def schoenfeld_residuals(
        ph_test_results: Dict,
        title: str = "Schoenfeld Residuals — Proportional Hazards Test",
    ) -> CanonicalPlot:
        """Gera plot de resíduos de Schoenfeld para teste de PH."""
        data = {
            'global_p': ph_test_results.get('global_p'),
            'by_variable': ph_test_results.get('by_variable', {}),
        }

        metadata = {
            'threshold': 0.05,
            'interpretation': {
                'p > 0.05': 'Proporcionalidade não rejeitada',
                'p <= 0.05': 'Possível violação de proporcionalidade',
            },
        }

        canonical_hash = hashlib.sha3_256(
            json.dumps({'data': data, 'metadata': metadata}, sort_keys=True).encode()
        ).hexdigest()

        return CanonicalPlot(
            plot_type='schoenfeld',
            title=title,
            data=data,
            metadata=metadata,
            canonical_hash=canonical_hash,
            generated_at=time.time(),
        )

    def render_to_png(self, plot: CanonicalPlot, width: int = 800, height: int = 600) -> bytes:
        """Renderiza CanonicalPlot para PNG (implementação simplificada)."""
        # Em produção: usar matplotlib/plotly com template canônico
        # Aqui: retornar placeholder
        import io
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)

            # Título
            draw.text((20, 20), plot.title, fill='black')

            # Tipo de plot
            draw.text((20, 50), f"Type: {plot.plot_type}", fill='gray')
            draw.text((20, 70), f"Hash: {plot.canonical_hash[:16]}...", fill='gray')

            # Placeholder para dados
            draw.text((20, 120), "[Plot data would render here]", fill='blue')

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        except ImportError:
            return b""
