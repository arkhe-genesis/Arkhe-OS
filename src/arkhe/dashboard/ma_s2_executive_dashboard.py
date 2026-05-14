#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ma_s2_executive_dashboard.py — Dashboard Executivo MA‑S2 em Tempo Real
Visualização de métricas de conformidade com alertas proativos e drill‑down por domínio.
"""

import asyncio, json, time, hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from arkhe.security.ma_s2_engine import MA_S2_ComplianceEngine, MA_S2_Domain, ComplianceStatus
from arkhe.core.temporal_chain import TemporalChain
from arkhe.security.guardian_attractor import GuardianAttractor
from arkhe.inventory.sbom_manager import SBOMManager
from arkhe.orchestrator.fleet_orchestrator import FleetOrchestrator

@dataclass
class ComplianceMetric:
    """Métrica de conformidade para visualização."""
    domain: MA_S2_Domain
    control_id: str
    status: ComplianceStatus
    last_updated: float
    evidence_hash: str
    sla_remaining_hours: Optional[float] = None
    trend: str = "stable"  # "improving", "degrading", "stable"

@dataclass
class ProactiveAlert:
    """Alerta proativo para liderança de segurança."""
    alert_id: str
    severity: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    domain: MA_S2_Domain
    control_id: Optional[str]
    recommended_action: str
    created_at: float
    acknowledged: bool = False
    temporal_anchor: Optional[str] = None

class MA_S2_ExecutiveDashboard:
    """
    Dashboard executivo para monitoramento de conformidade MA‑S2.
    Funcionalidades:
    • Visão geral de conformidade por domínio com semáforo (🟢/🟡/🔴)
    • Gráfico de tendência temporal de Φ_C e métricas de segurança
    • Lista de alertas proativos com priorização por impacto
    • Drill‑down para evidências e âncoras temporais verificáveis
    • Exportação de relatórios para auditoria externa
    """

    def __init__(self, engine: MA_S2_ComplianceEngine):
        self.engine = engine
        self.temporal = engine.temporal
        self.alert_engine = ProactiveAlertEngine(engine)
        self._cache: Dict[str, List[ComplianceMetric]] = {}
        self._last_refresh = 0

    def render(self):
        """Renderiza dashboard Streamlit."""
        st.set_page_config(
            page_title="ARKHE MA‑S2 Executive Dashboard",
            page_icon="🛡️",
            layout="wide",
        )

        # Header
        st.title("🛡️ ARKHE MA‑S2 Executive Dashboard")
        st.caption(f"Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            scope = st.selectbox("Escopo", ["full", "cvs", "apm", "inv", "aro"], index=0)
        with col2:
            time_range = st.selectbox("Período", ["24h", "7d", "30d", "all"], index=1)
        with col3:
            if st.button("🔄 Atualizar"):
                st.rerun()

        # Métricas principais (KPIs)
        self._render_kpi_cards(scope)

        # Gráficos principais
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            self._render_compliance_trend_chart(time_range)
        with col_chart2:
            self._render_domain_breakdown_chart(scope)

        # Alertas proativos
        self._render_proactive_alerts()

        # Tabela de controles com drill‑down
        self._render_controls_table(scope)

        # Footer com selo temporal
        st.divider()
        seal = self.temporal.current_seal
        st.caption(f"🔐 Selo temporal da sessão: `{seal[:24]}...` | [Verificar integridade](#)")

    def _render_kpi_cards(self, scope: str):
        """Renderiza cards de KPIs principais."""
        # Buscar métricas (cache de 5 min)
        if time.time() - self._last_refresh > 300:
            self._refresh_metrics(scope)
            self._last_refresh = time.time()

        metrics = self._cache.get(scope, [])

        # Calcular KPIs
        total_controls = len(metrics)
        compliant = sum(1 for m in metrics if m.status == ComplianceStatus.COMPLIANT)
        compliance_rate = compliant / total_controls if total_controls > 0 else 0

        critical_alerts = sum(1 for a in self.alert_engine.get_active_alerts() if a.severity == "critical")
        avg_sla_remaining = sum(m.sla_remaining_hours for m in metrics if m.sla_remaining_hours) / len([m for m in metrics if m.sla_remaining_hours]) if any(m.sla_remaining_hours for m in metrics) else None

        # Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="Taxa de Conformidade",
                value=f"{compliance_rate:.1%}",
                delta=f"{compliant}/{total_controls} controles",
                delta_color="normal" if compliance_rate >= 0.95 else "inverse",
            )
        with col2:
            st.metric(
                label="Φ_C Coerência",
                value=f"{self._get_current_phi_c():.4f}",
                delta="estável" if self._get_phi_c_trend() == "stable" else self._get_phi_c_trend(),
                delta_color="normal",
            )
        with col3:
            st.metric(
                label="Alertas Críticos",
                value=critical_alerts,
                delta="requer atenção" if critical_alerts > 0 else "nenhum",
                delta_color="inverse" if critical_alerts > 0 else "normal",
            )
        with col4:
            sla_label = f"{avg_sla_remaining:.1f}h" if avg_sla_remaining else "N/A"
            st.metric(
                label="SLA Médio Restante",
                value=sla_label,
                delta="dentro do prazo" if (avg_sla_remaining or 999) > 4 else "próximo do limite",
                delta_color="normal" if (avg_sla_remaining or 999) > 4 else "inverse",
            )

    def _render_compliance_trend_chart(self, time_range: str):
        """Renderiza gráfico de tendência de conformidade."""
        # Dados simulados para demonstração
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        compliance_rates = [0.92 + 0.08 * (i/30) + 0.02 * (0.5 - (i%7)/7) for i in range(30)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=compliance_rates,
            mode='lines+markers',
            name='Taxa de Conformidade',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=6, color='#27ae60'),
        ))
        fig.add_hline(y=0.95, line_dash="dash", line_color="#f39c12",
                     annotation_text="Target: 95%", annotation_position="top right")
        fig.update_layout(
            title="Tendência de Conformidade MA‑S2 (30 dias)",
            xaxis_title="Data",
            yaxis_title="Taxa de Conformidade",
            yaxis_range=[0.8, 1.0],
            hovermode='x unified',
            height=350,
            margin=dict(l=40, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_domain_breakdown_chart(self, scope: str):
        """Renderiza gráfico de breakdown por domínio."""
        metrics = self._cache.get(scope, [])

        # Agrupar por domínio
        domain_data = {}
        for domain in MA_S2_Domain:
            domain_metrics = [m for m in metrics if m.domain == domain]
            if domain_metrics:
                compliant = sum(1 for m in domain_metrics if m.status == ComplianceStatus.COMPLIANT)
                total = len(domain_metrics)
                domain_data[domain.value] = {
                    'compliant': compliant,
                    'total': total,
                    'rate': compliant/total if total > 0 else 0,
                }

        if not domain_data:
            st.info("Nenhum dado de conformidade disponível para o escopo selecionado.")
            return

        # Gráfico de barras horizontais
        df = pd.DataFrame([
            {
                'Domínio': d.replace('_', ' ').title(),
                'Conforme': data['compliant'],
                'Total': data['total'],
                'Taxa': data['rate'],
            }
            for d, data in domain_data.items()
        ])

        fig = px.bar(
            df, x='Taxa', y='Domínio', orientation='h',
            color='Taxa', color_continuous_scale=['#e74c3c', '#f39c12', '#2ecc71'],
            range_color=[0, 1],
            text='Taxa',
        )
        fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig.update_layout(
            title="Conformidade por Domínio MA‑S2",
            xaxis_title="Taxa de Conformidade",
            yaxis_title="",
            height=350,
            margin=dict(l=40, r=20, t=40, b=20),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_proactive_alerts(self):
        """Renderiza lista de alertas proativos."""
        alerts = self.alert_engine.get_active_alerts()

        st.subheader("🚨 Alertas Proativos")

        if not alerts:
            st.success("✅ Nenhum alerta ativo — conformidade estável")
            return

        # Filtrar por severidade
        severity_filter = st.multiselect(
            "Filtrar por severidade",
            ["critical", "high", "medium", "low"],
            default=["critical", "high"],
        )
        filtered_alerts = [a for a in alerts if a.severity in severity_filter]

        for alert in filtered_alerts:
            with st.expander(f"{'🔴' if alert.severity == 'critical' else '🟠' if alert.severity == 'high' else '🟡'} {alert.title}", expanded=alert.severity in ["critical", "high"]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Domínio**: `{alert.domain.value}`")
                    if alert.control_id:
                        st.markdown(f"**Controle**: `{alert.control_id}`")
                    st.markdown(f"**Descrição**: {alert.description}")
                    st.markdown(f"**Ação recomendada**: {alert.recommended_action}")
                with col2:
                    st.markdown(f"**Criado**: {datetime.fromtimestamp(alert.created_at).strftime('%H:%M')}")
                    if alert.temporal_anchor:
                        st.markdown(f"**Âncora**: `{alert.temporal_anchor[:12]}...`")
                    if st.button("✅ Reconhecer", key=f"ack_{alert.alert_id}"):
                        self.alert_engine.acknowledge_alert(alert.alert_id)
                        st.rerun()

    def _render_controls_table(self, scope: str):
        """Renderiza tabela de controles com drill‑down."""
        metrics = self._cache.get(scope, [])

        st.subheader("📋 Controles MA‑S2")

        if not metrics:
            st.info("Nenhum controle encontrado para o escopo selecionado.")
            return

        # Preparar dados para tabela
        data = []
        for m in metrics:
            data.append({
                "Domínio": m.domain.value,
                "Controle": m.control_id,
                "Status": "✅" if m.status == ComplianceStatus.COMPLIANT else "⚠️" if m.status == ComplianceStatus.PARTIAL else "❌",
                "Última Atualização": datetime.fromtimestamp(m.last_updated).strftime('%Y-%m-%d %H:%M'),
                "SLA Restante": f"{m.sla_remaining_hours:.1f}h" if m.sla_remaining_hours else "N/A",
                "Evidência": f"`{m.evidence_hash[:12]}...`",
            })

        df = pd.DataFrame(data)

        # Tabela interativa
        st.dataframe(
            df,
            column_config={
                "Status": st.column_config.TextColumn("Status", help="✅ Compliant, ⚠️ Partial, ❌ Non-compliant"),
                "Evidência": st.column_config.TextColumn("Evidência", help="Hash do artefato de evidência"),
            },
            use_container_width=True,
            hide_index=True,
        )

        # Drill‑down: clicar em evidência para ver detalhes
        selected = st.data_editor(df, disabled=True, key="controls_table")
        if selected is not None and not selected.empty:
            row = selected.iloc[0]
            with st.expander(f"🔍 Detalhes: {row['Controle']}"):
                st.markdown(f"**Evidência**: `{row['Evidência']}`")
                st.markdown(f"**Âncora temporal**: [Verificar na TemporalChain](#)")
                st.markdown(f"**SLA**: {row['SLA Restante']}")

    def _refresh_metrics(self, scope: str):
        """Atualiza cache de métricas."""
        # Em produção: consultar engine ou API
        # Para demo: gerar dados simulados
        metrics = []
        for domain in MA_S2_Domain:
            if scope != "full" and domain.value != scope:
                continue
            for i in range(5):  # 5 controles por domínio (simulado)
                status = ComplianceStatus.COMPLIANT if i < 4 else ComplianceStatus.PARTIAL
                metrics.append(ComplianceMetric(
                    domain=domain,
                    control_id=f"{domain.value.upper()}-{i+1:02d}",
                    status=status,
                    last_updated=time.time() - i * 3600,
                    evidence_hash=hashlib.sha3_256(f"{domain.value}-{i}".encode()).hexdigest(),
                    sla_remaining_hours=24 - i * 2 if status != ComplianceStatus.COMPLIANT else None,
                    trend="stable" if i % 3 == 0 else ("improving" if i % 3 == 1 else "degrading"),
                ))
        self._cache[scope] = metrics

    def _get_current_phi_c(self) -> float:
        """Obtém coerência Φ_C atual (simulado)."""
        # Em produção: consultar PhiCMonitor
        return 0.997 + 0.003 * (hash(self._last_refresh) % 100) / 100

    def _get_phi_c_trend(self) -> str:
        """Determina tendência de Φ_C (simulado)."""
        return ["stable", "improving", "degrading"][hash(self._last_refresh) % 3]


class ProactiveAlertEngine:
    """
    Motor de alertas proativos baseado em regras de conformidade.
    Detecta condições de risco antes que se tornem não-conformidades.
    """

    def __init__(self, engine: MA_S2_ComplianceEngine):
        self.engine = engine
        self.alerts: Dict[str, ProactiveAlert] = {}
        self._alert_counter = 0

    def get_active_alerts(self) -> List[ProactiveAlert]:
        """Retorna alertas ativos não reconhecidos."""
        # Para demo: gerar alertas simulados baseados em métricas
        if not self.alerts and time.time() % 3600 < 60:  # Gerar a cada hora
            self._generate_sample_alerts()

        return [a for a in self.alerts.values() if not a.acknowledged]

    def acknowledge_alert(self, alert_id: str):
        """Marca alerta como reconhecido."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True

    def _generate_sample_alerts(self):
        """Gera alertas de demonstração."""
        sample_alerts = [
            ProactiveAlert(
                alert_id=f"alert-{self._alert_counter}",
                severity="critical",
                title="SLA de resposta a CVE crítico próximo do limite",
                description="CVE-2026-12345 (CVSS 10.0) tem SLA de 4h; restam 45 minutos para mitigação.",
                domain=MA_S2_Domain.CVS,
                control_id="CVS-0.3",
                recommended_action="Acionar equipe de resposta a incidentes ou aplicar patch de emergência.",
                created_at=time.time(),
                temporal_anchor="a1b2c3d4e5f6...",
            ),
            ProactiveAlert(
                alert_id=f"alert-{self._alert_counter+1}",
                severity="high",
                title="Caminho de ataque de alto risco detectado",
                description="Caminho api-gateway → auth-service → database com score 0.92 e técnicas MITRE T1190+T1078.",
                domain=MA_S2_Domain.APM,
                control_id="APM-1.3",
                recommended_action="Revisar regras de WAF e implementar segmentação de rede adicional.",
                created_at=time.time() - 1800,
            ),
            ProactiveAlert(
                alert_id=f"alert-{self._alert_counter+2}",
                severity="medium",
                title="Drift de inventário detectado em ambiente prod",
                description="3 componentes presentes no runtime mas ausentes na SBOM mais recente.",
                domain=MA_S2_Domain.INV,
                control_id="INV-2.2",
                recommended_action="Reconciliar inventário e atualizar SBOM com componentes detectados.",
                created_at=time.time() - 7200,
            ),
        ]
        for a in sample_alerts:
            self.alerts[a.alert_id] = a
            self._alert_counter += 1


def main():
    """Ponto de entrada para execução do dashboard."""
    # Inicializar engine (em produção: injetar dependências reais)
    temporal = TemporalChain()
    engine = MA_S2_ComplianceEngine(
        temporal_chain=temporal,
        guardian=GuardianAttractor(),
        sbom_manager=SBOMManager(temporal_chain=temporal),
        orchestrator=FleetOrchestrator(temporal_chain=temporal),
    )

    dashboard = MA_S2_ExecutiveDashboard(engine)
    dashboard.render()


if __name__ == "__main__":
    main()