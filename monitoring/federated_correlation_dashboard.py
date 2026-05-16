import streamlit as st
import time
import pandas as pd
import numpy as np

st.set_page_config(page_title="Federated Correlation Dashboard", layout="wide", page_icon="🌐")

st.title("🌐 Sentinel Fabric - Federated Correlation Dashboard")
st.markdown("Visualização em tempo real de correlações anômalas cross-org e métricas de privacidade diferencial.")

# Simulação de dados
def generate_mock_data():
    return pd.DataFrame({
        "timestamp": pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(hours=24), periods=100, freq='15min'),
        "org_id": np.random.choice(["BancoDoBrasil", "Itau", "Bradesco", "Caixa", "Nubank"], 100),
        "anomaly_count": np.random.poisson(lam=5, size=100),
        "epsilon_noise": np.random.uniform(2.0, 5.0, 100)
    })

data = generate_mock_data()

# Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total IOCs Ingeridos (24h)", value=f"{data['anomaly_count'].sum():,}")

with col2:
    st.metric(label="Parceiros Ativos", value=f"{data['org_id'].nunique()}")

with col3:
    st.metric(label="Ruído DP (Epsilon Médio)", value=f"{data['epsilon_noise'].mean():.2f}")

st.divider()

st.subheader("📈 Ingestão de IOCs por Parceiro")
st.bar_chart(data.groupby("org_id")["anomaly_count"].sum())

st.subheader("🚨 Alertas Cross-Org Recentes")

alerts = [
    {"ID": "ALRT-1001", "Severidade": "🔴 Alta", "Orgs": "Itaú, Bradesco, Caixa", "Features": "Login Failed, IP Anômalo"},
    {"ID": "ALRT-1002", "Severidade": "🟡 Média", "Orgs": "BancoDoBrasil, Nubank", "Features": "Transferência Atípica"},
    {"ID": "ALRT-1003", "Severidade": "🔴 Crítica", "Orgs": "Todos", "Features": "Acesso root indevido"}
]

st.table(pd.DataFrame(alerts))

st.markdown("---")
st.caption("Arkhe OS Sentinel Fabric © 2024. Todos os eventos são ancorados via TemporalChain (PQC-safe).")
