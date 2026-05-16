#!/usr/bin/env python3
"""
Dashboard Unificado de Federação Global (Streamlit)
Visualiza métricas, modelos e alertas de múltiplas organizações participantes da federação.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Arkhe Global Federation", layout="wide", page_icon="🌐")

st.title("🌐 Arkhe Global Federation Dashboard")
st.markdown("Monitoramento unificado de ameaças cross-border, sincronização PQC e FedAvg em tempo real.")

# Mock Data
orgs = ["BancoDoBrasil (BR)", "Itaú (BR)", "Santander (EU)", "JPMorgan (US)"]
metrics = {
    "org": orgs,
    "phi_c": np.random.uniform(0.95, 0.999, len(orgs)),
    "epsilon_budget": np.random.uniform(2.0, 15.0, len(orgs)),
    "fedavg_rounds": [142, 142, 142, 142],
    "pqc_sync_status": ["Verified", "Verified", "Verified", "Verified"],
    "alerts_24h": np.random.randint(0, 5, len(orgs))
}

df = pd.DataFrame(metrics)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Organizações Conectadas", len(orgs))
col2.metric("Média Φ_C Global", f"{df['phi_c'].mean():.4f}")
col3.metric("Rounds FedAvg", 142)
col4.metric("Alertas Cross-Org (24h)", df['alerts_24h'].sum())

st.divider()

st.subheader("Estado dos Nós Federados")
st.dataframe(
    df.style.highlight_max(subset=['phi_c'], color='lightgreen')
            .highlight_max(subset=['alerts_24h'], color='lightcoral')
            .format({"phi_c": "{:.4f}", "epsilon_budget": "{:.2f}"}),
    use_container_width=True
)

st.divider()

col_map, col_alerts = st.columns([2, 1])

with col_map:
    st.subheader("Sincronização PQC e Privacidade Diferencial")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3) * [1, 2, 1.5] + [4, 5, 2],
        columns=['epsilon_consumed', 'phi_c_impact', 'sync_latency_ms']
    )
    st.line_chart(chart_data)

with col_alerts:
    st.subheader("Últimos Alertas (Sentinel)")
    alerts = [
        "🚨 Anomalia de Rede (BR/US) - Trust 92%",
        "🛡️ Consenso de Healing: Bloqueio de IP Malicioso",
        "⚠️ Epsilon Exausto: Santander (EU)",
        "✅ Novo Modelo FedAvg Sincronizado (Selo PQC: Validado)"
    ]
    for alert in alerts:
        if "🚨" in alert:
            st.error(alert)
        elif "⚠️" in alert:
            st.warning(alert)
        elif "✅" in alert:
            st.success(alert)
        else:
            st.info(alert)

st.caption(f"Última atualização: {time.strftime('%Y-%m-%d %H:%M:%S')}")
