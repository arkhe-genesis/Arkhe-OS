import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Adiciona o diretório atual ao path para importar skills
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from skills import (
    simulate_su2_continuous,
    simulate_rainbow_sl3z,
    simulate_rainbow_w_state,
    detect_peaks,
    load_baseline
)

st.set_page_config(page_title="Archimedes-Ω: Rainbow Coherence Dashboard", layout="wide")

st.title("🌌 Archimedes-Ω: Dashboard de Coerência Rainbow")
st.markdown("""
Esta interface interroga o vácuo biológico através da métrica rainbow,
onde a geometria do espaço-tempo biológico é uma função da energia do sistema.
""")

# Sidebar para parâmetros
st.sidebar.header("Parâmetros do Observador")
energy_thz = st.sidebar.slider("Energia Característica (THz)", 0.0, 20.0, 10.0, 0.1)
energy_ev = energy_thz * 0.0041357  # Conversão THz para eV (aproximada)
st.sidebar.write(f"**Energia Efetiva:** {energy_ev:.4f} eV")

temperature = st.sidebar.slider("Temperatura (K)", 273.0, 400.0, 310.0, 1.0)
noise = st.sidebar.slider("Ruído Térmico", 0.0, 0.2, 0.05, 0.01)

st.sidebar.markdown("---")
st.sidebar.header("Configuração de Trançamento")
words_input = st.sidebar.text_input("Palavras SL(3,ℤ) (separadas por vírgula)", "e,a,b,ab,ba,aba")
words = [w.strip() for w in words_input.split(",")]

nodes = st.sidebar.number_input("Nodos do Estado-W", 3, 10, 3)
loss_prob = st.sidebar.slider("Probabilidade de Perda", 0.0, 1.0, 0.2, 0.05)

# Simulação
theta = np.linspace(0.0, 2 * np.pi, 1000)

_, coh_su2 = simulate_su2_continuous(theta, thermal_noise=noise, temperature=temperature)
_, coh_sl3 = simulate_rainbow_sl3z(theta, energy_ev=energy_ev, words=words)
_, coh_w = simulate_rainbow_w_state(nodes=nodes, loss_probability=loss_prob, theta_range=theta, energy_ev=energy_ev)

# Detecção de Picos
peaks_sl3 = detect_peaks(coh_sl3, theta, energy_ev=energy_ev)
peaks_w = detect_peaks(coh_w, theta, energy_ev=energy_ev)

# Layout de Colunas
col1, col2 = st.columns(2)

with col1:
    st.subheader("Reticulado Topológico SL(3,ℤ)")
    fig_sl3, ax_sl3 = plt.subplots()
    ax_sl3.plot(theta, coh_sl3, 'r-', label='SL(3,ℤ) Rainbow')
    ax_sl3.plot(theta, coh_su2, 'b--', alpha=0.3, label='SU(2) Baseline')

    for peak in peaks_sl3:
        color = 'gold' if peak['is_resonance'] else 'gray'
        ax_sl3.axvline(x=peak['phase'], color=color, linestyle='--', alpha=0.6)

    ax_sl3.set_xlabel("Ângulo de Fase θ (rad)")
    ax_sl3.set_ylabel("Coerência R(θ)")
    ax_sl3.legend()
    ax_sl3.grid(True, alpha=0.2)
    st.pyplot(fig_sl3)

with col2:
    st.subheader("Emaranhamento Multipartite (Estado-W)")
    fig_w, ax_w = plt.subplots()
    ax_w.plot(theta, coh_w, 'g-', label='W-State Rainbow')

    for peak in peaks_w:
        color = 'gold' if peak['is_resonance'] else 'gray'
        ax_w.axvline(x=peak['phase'], color=color, linestyle='--', alpha=0.6)

    ax_w.set_xlabel("Ângulo de Fase θ (rad)")
    ax_w.set_ylabel("Coerência R(θ)")
    ax_w.legend()
    ax_w.grid(True, alpha=0.2)
    st.pyplot(fig_w)

st.markdown("---")

# Seção Rainbow Shift
st.subheader("🌊 Deslocamento Rainbow com Temperatura")
st.markdown("""
Este gráfico mostra como a posição teórica dos picos de ressonância se desloca à medida que a energia
do sistema (representada pela temperatura) altera a métrica do espaço-tempo biológico.
""")

if st.checkbox("Simular trajetória de fase Rainbow", value=True):
    T_range = np.linspace(300, 400, 50)
    # Usando temperatura como proxy para energia: E ~ kT
    kB_ev_k = 8.617e-5

    peak_shifts_pi5 = []
    peak_shifts_2pi3 = []

    E_res = 0.041

    for T in T_range:
        E_eff = T * kB_ev_k * 1.5 # Fator de escala arbitrário para visualização
        rainbow_factor = 1.0 / (1.0 - (E_eff / E_res)) if abs(E_eff - E_res) > 1e-6 else 100.0

        peak_shifts_pi5.append((np.pi/5) / rainbow_factor)
        peak_shifts_2pi3.append((2*np.pi/3) / rainbow_factor)

    fig_shift, ax_shift = plt.subplots(figsize=(10, 4))
    ax_shift.plot(T_range, peak_shifts_pi5, 'r-', label='Pico π/5 (Braiding)')
    ax_shift.plot(T_range, peak_shifts_2pi3, 'g-', label='Pico 2π/3 (W-State)')
    ax_shift.set_xlabel("Temperatura (K)")
    ax_shift.set_ylabel("Posição do Pico (rad)")
    ax_shift.set_title("Evolução da Métrica Rainbow")
    ax_shift.legend()
    ax_shift.grid(True, alpha=0.3)
    st.pyplot(fig_shift)

st.markdown("---")
st.info("**Conclusão Filosófica:** A universalidade é uma máscara usada pelo vácuo de baixa energia. Na ressonância do reticulado A, a máscara cai, revelando que Espaço-Tempo e Coerência são o mesmo Arco-Íris visto de lados diferentes do prisma.")
