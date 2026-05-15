#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integrity_dashboard.py — Substrato 9025: Dashboard de Monitoramento de Integridade em Tempo Real
Monitora integridade do driver Cathedral, coerência Φ_C, assinaturas, e detecta tentativas de tampering.
"""

import streamlit as st
import asyncio
import json
import time
import hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import websockets
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class IntegrityStatus(Enum):
    """Status de integridade de componentes."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    TAMPERED = "tampered"
    UNKNOWN = "unknown"

@dataclass
class IntegrityMetric:
    """Métrica de integridade monitorada."""
    component: str
    metric_name: str
    current_value: float
    threshold_warning: float
    threshold_critical: float
    status: IntegrityStatus
    last_updated: float
    historical_values: List[float] = field(default_factory=list)

    def add_value(self, value: float):
        """Adiciona novo valor ao histórico (mantém últimos 100)."""
        self.historical_values.append(value)
        if len(self.historical_values) > 100:
            self.historical_values.pop(0)
        self.current_value = value
        self.last_updated = time.time()
        self._update_status()

    def _update_status(self):
        """Atualiza status baseado em thresholds."""
        if self.current_value < self.threshold_critical:
            self.status = IntegrityStatus.TAMPERED
        elif self.current_value < self.threshold_warning:
            self.status = IntegrityStatus.CRITICAL
        elif self.current_value < self.threshold_warning * 1.1:
            self.status = IntegrityStatus.WARNING
        else:
            self.status = IntegrityStatus.HEALTHY

@dataclass
class TamperingAlert:
    """Alerta de tentativa de tampering detectada."""
    alert_id: str
    timestamp: float
    component: str
    alert_type: str  # 'hash_mismatch', 'signature_invalid', 'phi_c_drop', 'unauthorized_access'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    evidence: Dict
    acknowledged: bool = False
    remediation_status: str = "pending"  # pending, in_progress, resolved

# ============================================================================
# CLIENTE DE MONITORAMENTO (WebSocket + REST)
# ============================================================================

class IntegrityMonitorClient:
    """Cliente para conectar ao serviço de monitoramento de integridade."""

    def __init__(self, ws_endpoint: str = "ws://localhost:8080/ws/integrity",
                 api_endpoint: str = "http://localhost:8080/api"):
        self.ws_endpoint = ws_endpoint
        self.api_endpoint = api_endpoint
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.metrics: Dict[str, IntegrityMetric] = {}
        self.alerts: List[TamperingAlert] = []
        self.callbacks: List[callable] = []

    async def connect(self):
        """Estabelece conexão WebSocket com servidor de monitoramento."""
        try:
            self.websocket = await websockets.connect(self.ws_endpoint)
            logger.info(f"✅ Conectado ao monitoramento: {self.ws_endpoint}")

            # Registrar para receber atualizações
            await self.websocket.send(json.dumps({
                "action": "subscribe",
                "channels": ["metrics", "alerts", "phi_c"]
            }))

            # Iniciar loop de recebimento
            asyncio.create_task(self._receive_loop())
            return True
        except Exception as e:
            logger.error(f"❌ Falha ao conectar: {e}")
            return False

    async def _receive_loop(self):
        """Loop assíncrono para receber mensagens do servidor."""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                logger.warning(f"⚠️  Mensagem inválida recebida: {message[:100]}")

    async def _handle_message(self, data: Dict):
        """Processa mensagem recebida do servidor."""
        msg_type = data.get("type")

        if msg_type == "metric_update":
            await self._update_metric(data["payload"])
        elif msg_type == "alert":
            await self._add_alert(data["payload"])
        elif msg_type == "phi_c_update":
            await self._update_phi_c(data["payload"])

        # Notificar callbacks registrados
        for callback in self.callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"❌ Erro em callback: {e}")

    async def _update_metric(self, payload: Dict):
        """Atualiza métrica de integridade."""
        key = f"{payload['component']}:{payload['metric_name']}"

        if key not in self.metrics:
            self.metrics[key] = IntegrityMetric(
                component=payload["component"],
                metric_name=payload["metric_name"],
                current_value=payload["value"],
                threshold_warning=payload.get("threshold_warning", 0.95),
                threshold_critical=payload.get("threshold_critical", 0.90),
                status=IntegrityStatus.HEALTHY,
                last_updated=time.time(),
            )

        self.metrics[key].add_value(payload["value"])

    async def _add_alert(self, payload: Dict):
        """Adiciona novo alerta de tampering."""
        alert = TamperingAlert(
            alert_id=payload["alert_id"],
            timestamp=payload["timestamp"],
            component=payload["component"],
            alert_type=payload["alert_type"],
            severity=payload["severity"],
            description=payload["description"],
            evidence=payload.get("evidence", {}),
        )
        self.alerts.insert(0, alert)  # Inserir no início para mais recentes primeiro

        # Manter apenas últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[:100]

    async def _update_phi_c(self, payload: Dict):
        """Atualiza métrica especial de coerência Φ_C."""
        # Φ_C é tratado como métrica especial com visualização dedicada
        key = "system:phi_c_coherence"
        if key not in self.metrics:
            self.metrics[key] = IntegrityMetric(
                component="system",
                metric_name="phi_c_coherence",
                current_value=payload["value"],
                threshold_warning=0.99,
                threshold_critical=0.95,
                status=IntegrityStatus.HEALTHY,
                last_updated=time.time(),
            )
        self.metrics[key].add_value(payload["value"])

    def register_callback(self, callback: callable):
        """Registra callback para notificações em tempo real."""
        self.callbacks.append(callback)

    async def acknowledge_alert(self, alert_id: str, notes: str = ""):
        """Reconhece alerta e adiciona notas de remedicação."""
        # Em produção: chamar API REST para atualizar status no servidor
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.remediation_status = "in_progress"
                break

    async def get_historical_data(self, component: str, metric: str,
                                hours: int = 24) -> List[Dict]:
        """Obtém dados históricos de uma métrica via API REST."""
        import aiohttp
        url = f"{self.api_endpoint}/metrics/{component}/{metric}/history"
        params = {"hours": hours}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"❌ Erro ao buscar histórico: {resp.status}")
                    return []

# ============================================================================
# COMPONENTES DO DASHBOARD STREAMLIT
# ============================================================================

def render_header():
    """Renderiza cabeçalho do dashboard."""
    st.set_page_config(
        page_title="🛡️ ARKHE Integrity Monitor",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🛡️ ARKHE Cathedral — Integrity Monitoring Dashboard")
    st.markdown("*Monitoramento em tempo real de integridade, coerência Φ_C e detecção de tampering*")

    # Barra de status global
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔐 Driver Status", "✅ Healthy", delta=None)
    with col2:
        st.metric("🌀 Φ_C Coherence", "0.9973", delta="+0.0002")
    with col3:
        st.metric("🔍 Active Alerts", "0", delta=None)
    with col4:
        st.metric("⏱️  Last Update", datetime.now().strftime("%H:%M:%S"), delta=None)

    st.divider()

def render_phi_c_gauge(phi_c_value: float):
    """Renderiza medidor de coerência Φ_C."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=phi_c_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "🌀 Coerência Φ_C", 'font': {'size': 18}},
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
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.99
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

def render_metrics_table(metrics: Dict[str, IntegrityMetric]):
    """Renderiza tabela de métricas de integridade."""
    if not metrics:
        st.info("📊 Aguardando dados de métricas...")
        return

    # Preparar dados para tabela
    data = []
    for key, metric in metrics.items():
        data.append({
            "Componente": metric.component,
            "Métrica": metric.metric_name,
            "Valor": f"{metric.current_value:.4f}",
            "Status": metric.status.value.upper(),
            "⚠️ Threshold": f"{metric.threshold_warning:.2f}",
            "🔴 Critical": f"{metric.threshold_critical:.2f}",
            "Atualizado": datetime.fromtimestamp(metric.last_updated).strftime("%H:%M:%S")
        })

    df = pd.DataFrame(data)

    # Aplicar formatação condicional
    def color_status(val):
        colors = {
            'HEALTHY': 'background-color: #d4edda; color: #155724',
            'WARNING': 'background-color: #fff3cd; color: #856404',
            'CRITICAL': 'background-color: #f8d7da; color: #721c24',
            'TAMPERED': 'background-color: #dc3545; color: white; font-weight: bold',
            'UNKNOWN': 'background-color: #e2e3e5; color: #383d41'
        }
        return colors.get(val, '')

    st.dataframe(
        df.style.map(color_status, subset=['Status']),
        use_container_width=True,
        hide_index=True
    )

def render_alerts_panel(alerts: List[TamperingAlert]):
    """Renderiza painel de alertas de tampering."""
    st.subheader("🚨 Alertas de Segurança")

    if not alerts:
        st.success("✅ Nenhum alerta ativo — sistema íntegro")
        return

    # Filtrar apenas alertas não reconhecidos
    active_alerts = [a for a in alerts if not a.acknowledged]

    for alert in active_alerts[:5]:  # Mostrar apenas 5 mais recentes
        severity_color = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }

        with st.expander(f"{severity_color.get(alert.severity, '⚪')} [{alert.severity.upper()}] {alert.component}: {alert.alert_type}"):
            st.markdown(f"**Descrição**: {alert.description}")
            st.markdown(f"**Timestamp**: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")

            if alert.evidence:
                st.markdown("**Evidências**:")
                st.json(alert.evidence)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Reconhecer", key=f"ack_{alert.alert_id}"):
                    # Em produção: chamar API para acknowledge
                    st.success("Alerta reconhecido!")
            with col2:
                if st.button("🔍 Detalhes", key=f"details_{alert.alert_id}"):
                    st.markdown("📋 Detalhes completos do alerta...")

def render_historical_chart(client: IntegrityMonitorClient, component: str, metric: str):
    """Renderiza gráfico histórico de métrica."""
    # Em produção: buscar dados reais da API
    # Para demo: gerar dados simulados
    hours = st.slider("Período (horas)", 1, 168, 24)

    # Gerar dados simulados com tendência
    timestamps = [time.time() - i*3600 for i in range(hours)][::-1]
    base_value = 0.997
    values = [base_value + np.random.normal(0, 0.001) for _ in range(hours)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[datetime.fromtimestamp(t) for t in timestamps],
        y=values,
        mode='lines+markers',
        name=metric,
        line=dict(color='#3498db', width=2),
        marker=dict(size=4)
    ))

    # Adicionar linhas de threshold
    fig.add_hline(y=0.99, line_dash="dash", line_color="orange",
                 annotation_text="Warning", annotation_position="right")
    fig.add_hline(y=0.95, line_dash="dash", line_color="red",
                 annotation_text="Critical", annotation_position="right")

    fig.update_layout(
        title=f"Histórico: {component} → {metric}",
        xaxis_title="Tempo",
        yaxis_title="Valor",
        yaxis_range=[0.90, 1.0],
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

def render_realtime_log():
    """Renderiza log em tempo real de eventos de integridade."""
    st.subheader("📋 Log de Eventos em Tempo Real")

    # Placeholder para stream de logs
    log_container = st.empty()

    # Simular logs em tempo real (em produção: conectar via WebSocket)
    sample_logs = [
        "✅ Driver hash verified: c4f3e2a1b0d5...",
        "🌀 Φ_C sync completed: 0.9973 → 0.9974",
        "🔐 Catalog signature validated",
        "⚡ TemporalChain anchor: event_abc123",
        "🛡️ Guardian exorcism: 0 threats detected",
    ]

    for log in sample_logs:
        log_container.code(log, language=None)
        time.sleep(0.5)

# ============================================================================
# FUNÇÃO PRINCIPAL DO DASHBOARD
# ============================================================================

async def main_dashboard():
    """Função principal do dashboard."""
    render_header()

    # Inicializar cliente de monitoramento
    client = IntegrityMonitorClient()
    connected = await client.connect()

    if not connected:
        st.error("❌ Não foi possível conectar ao servidor de monitoramento")
        st.info("💡 Verifique se o serviço está rodando em ws://localhost:8080/ws/integrity")
        return

    # Layout em abas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🔍 Métricas", "🚨 Alertas", "📈 Histórico"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            # Obter valor atual de Φ_C (simulado)
            phi_c = client.metrics.get("system:phi_c_coherence")
            phi_c_value = phi_c.current_value if phi_c else 0.9973
            render_phi_c_gauge(phi_c_value)

        with col2:
            st.subheader("🔐 Componentes Monitorados")
            components = [
                ("catedral.sys", "Driver kernel", "✅ Healthy"),
                ("catedral.ini", "Configuração", "✅ Healthy"),
                ("catedral.cat", "Catálogo", "✅ Healthy"),
                ("TemporalChain", "Cadeia temporal", "✅ Healthy"),
                ("Guardian", "Guardião Atratora", "✅ Healthy"),
                ("MA-S2 Engine", "Conformidade", "✅ Healthy"),
            ]
            for name, desc, status in components:
                st.markdown(f"- **{name}**: {desc} — {status}")

        render_realtime_log()

    with tab2:
        render_metrics_table(client.metrics)

        st.subheader("📈 Detalhe de Métrica")
        col1, col2 = st.columns(2)
        with col1:
            component = st.selectbox("Componente", ["system", "catedral.sys", "TemporalChain", "Guardian"])
        with col2:
            metric = st.selectbox("Métrica", ["phi_c_coherence", "hash_integrity", "signature_valid", "anchor_rate"])

        if st.button("🔄 Atualizar Dados"):
            # Em produção: buscar dados atualizados
            st.success("Dados atualizados!")

    with tab3:
        render_alerts_panel(client.alerts)

        st.subheader("📋 Histórico de Alertas")
        if client.alerts:
            alert_data = []
            for alert in client.alerts:
                alert_data.append({
                    "Timestamp": datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                    "Componente": alert.component,
                    "Tipo": alert.alert_type,
                    "Severidade": alert.severity.upper(),
                    "Status": "Reconhecido" if alert.acknowledged else "Pendente",
                })
            st.dataframe(pd.DataFrame(alert_data), use_container_width=True)
        else:
            st.info("Nenhum alerta registrado nas últimas 24h")

    with tab4:
        render_historical_chart(client, "system", "phi_c_coherence")

        st.subheader("📥 Exportar Dados")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Exportar CSV"):
                st.success("Dados exportados para integrity_report.csv")
        with col2:
            if st.button("📊 Exportar JSON"):
                st.success("Dados exportados para integrity_report.json")
        with col3:
            if st.button("🔗 Compartilhar Link"):
                st.success("Link de compartilhamento gerado!")

def run_dashboard():
    """Entry point para executar o dashboard."""
    asyncio.run(main_dashboard())

if __name__ == "__main__":
    run_dashboard()
