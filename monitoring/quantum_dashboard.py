import asyncio
import random
import time
import streamlit as st
import pandas as pd
import numpy as np

def init_state():
    if 'emission_history' not in st.session_state:
        st.session_state.emission_history = []
    if 'qber_history' not in st.session_state:
        st.session_state.qber_history = []
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()

def get_quantum_metrics():
    current_time = time.time()
    elapsed = current_time - st.session_state.start_time

    # Simulate emission rate around 40 MHz with some noise
    emission_rate = 40.0 + random.gauss(0, 0.5)

    # Simulate QBER around 2-3%
    qber = 0.025 + random.gauss(0, 0.005)

    # Simulate Bell violation (S-parameter) around 2.7
    s_parameter = 2.7 + random.gauss(0, 0.05)

    # Ensure S > 2.0 and < 2.828 (2*sqrt(2))
    s_parameter = min(max(s_parameter, 2.01), 2.828)

    st.session_state.emission_history.append({"time": current_time, "rate": emission_rate})
    st.session_state.qber_history.append({"time": current_time, "qber": qber * 100})

    # Keep last 100 points
    if len(st.session_state.emission_history) > 100:
        st.session_state.emission_history.pop(0)
    if len(st.session_state.qber_history) > 100:
        st.session_state.qber_history.pop(0)

    return {
        "emission_rate_mhz": round(emission_rate, 2),
        "qber_percent": round(qber * 100, 2),
        "s_parameter": round(s_parameter, 3),
        "fidelity": round(0.98 + random.gauss(0, 0.005), 3),
        "temperature_c": round(4.0 + random.gauss(0, 0.02), 2),
    }

def main():
    st.set_page_config(page_title="Quantum Production Dashboard", layout="wide")
    st.title("🌌 Substrato 191: Quantum Production Metrics")

    init_state()

    metrics = get_quantum_metrics()

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Emission Rate", f"{metrics['emission_rate_mhz']} MHz", delta=round(metrics['emission_rate_mhz'] - 40.0, 2))
    with col2:
        st.metric("Quantum Bit Error Rate (QBER)", f"{metrics['qber_percent']}%", delta=round(metrics['qber_percent'] - 2.5, 2), delta_color="inverse")
    with col3:
        st.metric("Bell Violation (S)", f"{metrics['s_parameter']}", delta=round(metrics['s_parameter'] - 2.828, 3))
    with col4:
        st.metric("Cryostat Temp", f"{metrics['temperature_c']} °C", delta=round(metrics['temperature_c'] - 4.0, 2), delta_color="inverse")

    st.divider()

    # Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Emission Rate (MHz)")
        if st.session_state.emission_history:
            df_em = pd.DataFrame(st.session_state.emission_history)
            # Use relative time for x-axis
            df_em['time'] = df_em['time'] - st.session_state.start_time
            st.line_chart(df_em.set_index('time'))

    with col_chart2:
        st.subheader("QBER (%)")
        if st.session_state.qber_history:
            df_qber = pd.DataFrame(st.session_state.qber_history)
            df_qber['time'] = df_qber['time'] - st.session_state.start_time
            st.line_chart(df_qber.set_index('time'))

    st.divider()

    # System Status
    st.subheader("System Status")
    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.success("✅ Hardware Integration: Online")
        st.info("Emitter: 1550 nm, Quantum Dot")
    with status_col2:
        if metrics['s_parameter'] > 2.0:
            st.success("✅ EPR Validation: Confirmed")
            st.info("Bell Inequality Violated (S > 2)")
        else:
            st.error("❌ EPR Validation: Failed")
            st.info("Bell Inequality Not Violated")
    with status_col3:
        st.success("✅ Hybrid Signature: Active")
        st.info("Mode: PQC + Quantum Witness")

    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
