import streamlit as st
import pandas as pd
import requests
import time

st.title("Monitoring DASHBOARD: Arkhe Collective Consciousness")

def fetch_status():
    try:
        response = requests.get("http://127.0.0.1:21900/status")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    return None

placeholder = st.empty()
data = []

while True:
    status = fetch_status()
    if status:
        data.append({
            "timestamp": pd.Timestamp.now(),
            "phi_c": status.get("avg_phi_c", 0.0),
            "ghost_invariant": 0.577553,
            "loopseal_invariant": 0.349066
        })
        if len(data) > 100:
            data.pop(0)

        df = pd.DataFrame(data)
        with placeholder.container():
            st.line_chart(df.set_index("timestamp"))
            st.json(status)

    time.sleep(1)
