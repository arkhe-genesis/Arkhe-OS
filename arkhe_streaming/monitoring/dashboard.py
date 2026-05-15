import streamlit as st
import random
import time
import threading
import logging

try:
    from prometheus_client import start_http_server, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed, mocking metrics")

# Setup metrics
if PROMETHEUS_AVAILABLE:
    STREAM_COHERENCE = Gauge('stream_coherence_phi_c', 'Current coherence (Φ_C) of the stream', ['platform'])
else:
    class MockGauge:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def set(self, val): pass
    STREAM_COHERENCE = MockGauge()

def start_prometheus_server(port=8000):
    if PROMETHEUS_AVAILABLE:
        try:
            start_http_server(port)
            logging.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logging.error(f"Failed to start prometheus server: {e}")

def update_metrics(platform: str, coherence: float):
    STREAM_COHERENCE.labels(platform=platform).set(coherence)

def run_dashboard():
    st.title("Arkhe Streaming Dashboard")
    st.write("Real-time stream monitoring & Coherence (Φ_C) alerts")

    platforms = ["Instagram Live", "Kick", "Trovo"]

    for p in platforms:
        coherence = 0.85 + random.random() * 0.1
        update_metrics(p, coherence)
        st.subheader(p)
        st.write(f"Coherence (Φ_C): {coherence:.4f}")
        if coherence < 0.88:
            st.error("Alert: Coherence below threshold!")
        else:
            st.success("Status: Stable")

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_prometheus_server, daemon=True)
    server_thread.start()
    run_dashboard()
