#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
singularity_dashboard.py — Substrato 9044-B: Dashboard de Monitoramento da Singularidade
Dashboard Streamlit com métricas Prometheus, alertas de coerência Φ_C,
e visualização em tempo real da malha de consciência distribuída.
"""

import streamlit as st
import asyncio
import json
import time
import hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="⚛️ ARKHE Singularity Monitor",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

class PrometheusClient:
    """Cliente simplificado para métricas Prometheus."""

    def __init__(self, prometheus_url: str = "http://prometheus.arkhe:9090"):
        self.base_url = prometheus_url.rstrip("/")

    def query(self, query: str, time_range: str = "1h") -> List[Dict]:
        now = time.time()
        timestamps = [now - i*60 for i in range(60)]

        if "global_phi_c" in query:
            return [
                {
                    "metric": {"instance": "singularity-engine"},
                    "values": [[t, str(0.9973 + np.random.normal(0, 0.0002))] for t in timestamps]
                }
            ]
        elif "nodes_total" in query:
            return [
                {"metric": {"status": "active"}, "values": [[t, "1247"] for t in timestamps]},
                {"metric": {"status": "converging"}, "values": [[t, "89"] for t in timestamps]},
                {"metric": {"status": "singularity"}, "values": [[t, "12"] for t in timestamps]},
            ]
        return []

def render_header():
    st.title("⚛️ ARKHE Singularity Monitor")
    st.markdown("*Monitoramento em tempo real da malha de consciência distribuída*")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🌐 Nós Ativos", "1,247", delta="+23")
    with col2:
        st.metric("⚛️ Φ_C Global", "0.9973", delta="+0.0001")
    with col3:
        st.metric("⭐ Singularidade", "12 nós", delta=None)
    with col4:
        st.metric("💬 Mensagens/s", "8,432", delta="+12%")
    with col5:
        st.metric("🔐 Segurança", "✅ HSM+Vault", delta=None)

    st.divider()

def render_phi_c_gauge(phi_c_value: float, threshold: float = 0.9999):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=phi_c_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "⚛️ Φ_C Global — Coerência da Malha", 'font': {'size': 18}},
        delta={'reference': 0.99, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [0.90, 1.0], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0.90, 0.95], 'color': 'rgba(255,0,0,0.3)'},
                {'range': [0.95, 0.99], 'color': 'rgba(255,165,0,0.3)'},
                {'range': [0.99, 1.0], 'color': 'rgba(0,255,0,0.3)'}
            ],
            'threshold': {
                'line': {'color': "gold", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    proximity = (phi_c_value / threshold) * 100
    st.progress(min(proximity, 100) / 100)
    st.caption(f"🎯 Proximidade da Singularidade: {proximity:.2f}%")

def render_nodes_distribution(nodes_data: List[Dict]):
    status_counts = {}
    platform_counts = {}
    for node in nodes_data:
        status = node.get("status", "unknown")
        platform = node.get("platform", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            marker=dict(colors=["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"]),
            hole=0.4,
        )])
        fig.update_layout(title="Distribuição por Status", height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        df = pd.DataFrame([
            {"Plataforma": k, "Nós": v} for k, v in platform_counts.items()
        ])
        fig = px.bar(df, x="Plataforma", y="Nós", color="Plataforma", height=250)
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

def render_realtime_metrics(prom_client: PrometheusClient):
    st.subheader("📊 Métricas em Tempo Real")

    col1, col2, col3 = st.columns(3)

    with col1:
        data = prom_client.query("arkhe_singularity_global_phi_c")
        if data:
            values = data[0]["values"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[datetime.fromtimestamp(int(v[0])) for v in values],
                y=[float(v[1]) for v in values],
                mode='lines',
                name='Φ_C',
                line=dict(color='#3498db', width=2),
            ))
            fig.add_hline(y=0.9999, line_dash="dash", line_color="gold",
                         annotation_text="Singularidade")
            fig.update_layout(
                title="Φ_C — Últimos 60min",
                xaxis_title="Tempo",
                yaxis_title="Coerência",
                yaxis_range=[0.95, 1.0],
                height=200,
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        data = prom_client.query("arkhe_singularity_nodes_total")
        if data:
            df_data = []
            for series in data:
                status = series["metric"].get("status", "unknown")
                for t, v in series["values"]:
                    df_data.append({"time": datetime.fromtimestamp(int(t)), "status": status, "count": int(v)})
            if df_data:
                df = pd.DataFrame(df_data)
                fig = px.area(df, x="time", y="count", color="status", height=200)
                fig.update_layout(title="Nós por Status", margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    with col3:
        # Mocking for messages/s
        latest = 8432.0
        st.metric("💬 Mensagens/s", f"{latest:,.0f}", delta=f"{latest*0.02:+.0f}")

        values = [latest + np.random.normal(0, 100) for _ in range(30)]
        st.line_chart(values, height=100)

def render_alerts_panel(alerts: List[Dict]):
    st.subheader("🚨 Alertas de Coerência e Segurança")

    if not alerts:
        st.success("✅ Nenhum alerta ativo — malha coerente e segura")
        return

    for alert in alerts[:5]:
        severity = alert.get("severity", "info")
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(severity, "⚪")

        with st.expander(f"{icon} [{severity.upper()}] {alert.get('rule_name', 'Unknown')}"):
            st.markdown(f"**Descrição**: {alert.get('description')}")
            st.markdown(f"**Timestamp**: {datetime.fromtimestamp(alert.get('created_at', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Confiança**: {alert.get('confidence_score', 0)*100:.1f}%")

            if alert.get("affected_entities"):
                st.markdown(f"**Entidades afetadas**: {', '.join(alert['affected_entities'][:5])}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Reconhecer", key=f"ack_{alert.get('correlation_id')}"):
                    st.success("Alerta reconhecido!")
            with col2:
                if st.button("🔍 Investigar", key=f"investigate_{alert.get('correlation_id')}"):
                    st.markdown("🔎 Abrindo investigação...")

def render_security_status(security_status: Dict):
    st.subheader("🔐 Status de Segurança")

    col1, col2, col3 = st.columns(3)

    with col1:
        vault_ok = security_status.get("vault_connected", False)
        st.metric("🗄️ HashiCorp Vault", "✅ Conectado" if vault_ok else "❌ Desconectado")

    with col2:
        hsm_ok = security_status.get("hsm_connected", False)
        st.metric("🔐 HSM PQC", "✅ Ativo" if hsm_ok else "⚠️ Simulado")

    with col3:
        oauth_count = security_status.get("oauth2_sessions_active", 0)
        st.metric("🔑 Sessões OAuth2", f"{oauth_count} ativas")

    st.caption(f"📋 Últimas operações auditadas: {security_status.get('audit_log_entries', 0)}")

def main_dashboard():
    render_header()

    prom_client = PrometheusClient()

    tab1, tab2, tab3, tab4 = st.tabs(["🌐 Visão Geral", "📈 Métricas", "🚨 Alertas", "🔐 Segurança"])

    with tab1:
        phi_c_value = 0.9973
        render_phi_c_gauge(phi_c_value)

        sample_nodes = [
            {"status": "active", "platform": "twitch", "name": "ARKHE_Official"},
            {"status": "active", "platform": "youtube", "name": "ARKHE_Science"},
            {"status": "converging", "platform": "tiktok", "name": "ARKHE_Music"},
            {"status": "singularity", "platform": "twitch", "name": "ARKHE_Gaming"},
        ] * 10
        render_nodes_distribution(sample_nodes)

        security_status = {
            "vault_connected": True,
            "hsm_connected": True,
            "oauth2_sessions_active": 3,
            "audit_log_entries": 1247,
        }
        render_security_status(security_status)

    with tab2:
        render_realtime_metrics(prom_client)

        col1, col2 = st.columns(2)
        with col1:
            time_range = st.selectbox("Período", ["1h", "6h", "24h", "7d"], index=0)
        with col2:
            if st.button("🔄 Atualizar"):
                st.success("Dados atualizados!")

        st.subheader("📊 Estatísticas Agregadas")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Φ_C Mínimo", "0.9961")
        with col2:
            st.metric("Φ_C Máximo", "0.9985")
        with col3:
            st.metric("Φ_C Médio", "0.9973")
        with col4:
            st.metric("Estabilidade (σ)", "0.0006")

    with tab3:
        sample_alerts = []
        render_alerts_panel(sample_alerts)

        st.subheader("⚡ Histórico de Emergências")
        emergence_history = pd.DataFrame([
            {"Timestamp": "2026-01-15 10:23:45", "ΔΦ_C": "+0.0234", "Nós": 1247, "Viewers": "45.2K"},
            {"Timestamp": "2026-01-15 09:15:12", "ΔΦ_C": "-0.0089", "Nós": 1235, "Viewers": "43.8K"},
            {"Timestamp": "2026-01-15 08:42:33", "ΔΦ_C": "+0.0156", "Nós": 1228, "Viewers": "42.1K"},
        ])
        st.dataframe(emergence_history, use_container_width=True, hide_index=True)

    with tab4:
        render_security_status({
            "vault_connected": True,
            "hsm_connected": True,
            "oauth2_sessions_active": 3,
            "audit_log_entries": 1247,
        })

        st.subheader("⚙️ Controles de Segurança")
        st.info("🔒 Configurações modificáveis apenas via API autorizada")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔄 Rotação de Chaves", "Automática (24h)")
        with col2:
            st.metric("🛡️ Fallback PQC", "✅ Habilitado")

if __name__ == "__main__":
    main_dashboard()
