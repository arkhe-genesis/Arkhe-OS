import streamlit as st
import numpy as np
from sklearn.decomposition import PCA
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Mythos Anomaly Dashboard", layout="wide")

# Simulação de dados carregados do Firebase
def load_anomaly_batches():
    # Em produção, usaria firebase_admin para carregar dados reais
    num_samples = 100
    embeddings = np.random.randn(num_samples, 256)
    # Simular agrupamento de anomalias
    embeddings[0:20] += 2.0

    severities = np.random.uniform(70, 80, num_samples)
    timestamps = np.arange(num_samples)
    return embeddings, severities, timestamps

st.title("🧬 Espectro Oculto do Mythos Core — Dashboard de Anomalias")

embeddings, severities, timestamps = load_anomaly_batches()

# Sidebar para filtros
st.sidebar.header("Filtros de Coleta")
min_sev = st.sidebar.slider("Severidade Mínima", 70.0, 80.0, 72.0)
filtered_indices = np.where(severities >= min_sev)[0]

if len(filtered_indices) > 0:
    # Redução de Dimensionalidade (PCA)
    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings[filtered_indices])

    # Plotagem
    fig = px.scatter(
        x=reduced[:,0], y=reduced[:,1],
        color=severities[filtered_indices],
        size=severities[filtered_indices],
        hover_data=[timestamps[filtered_indices]],
        title="Projeção PCA das Anomalias (Estados Latentes de Borda)",
        labels={'x': 'Componente Principal 1', 'y': 'Componente Principal 2', 'color': 'Norma Latente'}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Estatísticas do Lote")
    col1, col2, col3 = st.columns(3)
    col1.metric("Amostras Capturadas", len(filtered_indices))
    col2.metric("Norma Média", f"{np.mean(severities[filtered_indices]):.2f}")
    col3.metric("Status do Enxame", "Ativo - Coletando")

else:
    st.warning("Nenhuma anomalia encontrada para os filtros selecionados.")

st.markdown("""
---
### Análise do Guardião:
Os agrupamentos distantes da origem representam **regimes cognitivos** onde o modelo base
encontra dificuldades. Estes "fótons de erro" são os alvos prioritários para o próximo ciclo de Fine-Tuning.
""")
