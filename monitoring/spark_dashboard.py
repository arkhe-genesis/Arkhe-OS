import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

def render_spark_metrics(prom_client):
    """Renderiza métricas específicas do Spark."""
    st.subheader("⚡ Métricas do Spark Streaming")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Throughput atual
        data = prom_client.query("rate(arkhe_spark_messages_processed_total[1m])")
        if data and data[0]["values"]:
            current_rate = float(data[0]["values"][-1][1])
            st.metric("📥 Throughput", f"{current_rate:,.0f} msgs/s")

    with col2:
        # Latência p99
        data = prom_client.query("histogram_quantile(0.99, rate(arkhe_spark_processing_latency_seconds_bucket[5m]))")
        if data and data[0]["values"]:
            p99 = float(data[0]["values"][-1][1])
            st.metric("⏱️ Latência P99", f"{p99*1000:.1f}ms")

    with col3:
        # Kafka consumer lag
        data = prom_client.query("kafka_consumer_lag{topic='chat_messages'}")
        if data and data[0]["values"]:
            lag = int(float(data[0]["values"][-1][1]))
            st.metric("📦 Kafka Lag", f"{lag:,}")

    # Gráfico de throughput histórico
    data = prom_client.query("rate(arkhe_spark_messages_processed_total[1m])")
    if data:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[datetime.fromtimestamp(int(v[0])) for v in data[0]["values"]],
            y=[float(v[1]) for v in data[0]["values"]],
            mode='lines',
            name='Throughput',
        ))
        fig.update_layout(
            title="Throughput de Processamento — Últimos 60min",
            xaxis_title="Tempo",
            yaxis_title="Mensagens/s",
            height=250,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
