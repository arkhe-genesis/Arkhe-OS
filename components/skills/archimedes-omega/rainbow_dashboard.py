import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import json
import openai
import os

# --- Configuração da Página ---
st.set_page_config(
    page_title="Arkhe-Ω Rainbow Coherence & Xenoactualization",

# --- Configuração da Página ---
st.set_page_config(
    page_title="Arkhe-Ω Rainbow Coherence",
    page_icon="🌈",
    layout="wide"
)

API_BASE = "http://localhost:8080"
MESH_API_BASE = "http://localhost:9337/v1"

# --- Funções de API ---

def fetch_rainbow_coherence(energy_thz: float, num_points: int = 1000):
# --- Funções de API ---
API_BASE = "http://localhost:8080" # Updated to match local dev server

def fetch_rainbow_coherence(energy_thz: float, num_points: int = 1000):
    """Fetch rainbow coherence data from API."""
    try:
        response = requests.post(
            f"{API_BASE}/simulate/rainbow-coherence",
            json={"energy_thz": energy_thz, "num_points": num_points}
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return calculate_local_rainbow(energy_thz, num_points)

def calculate_local_rainbow(energy_thz, num_points):
    PLANCK_ENERGY_EV = 1.22e28
    energy_ev = energy_thz * 4.135667662e-15 * 1e12
    f_e = 1.0 + (energy_ev / (PLANCK_ENERGY_EV * 1e-25))
    theta = np.linspace(0, 2 * np.pi, num_points)
    shift_fib = (np.pi / 5) * f_e
    shift_wstate = (2 * np.pi / 3) * f_e
    width_fib, width_wstate = 0.05 * f_e, 0.08 * f_e
    base_noise = 0.2 * np.exp(-energy_thz * 0.01)
        else:
            return calculate_local(energy_thz, num_points)
    except Exception as e:
        # Fallback to local calculation if API unavailable
        return calculate_local(energy_thz, num_points)

def calculate_local(energy_thz, num_points):
    """Local calculation fallback."""
    PLANCK_ENERGY_EV = 1.22e28
    energy_ev = energy_thz * 4.135667662e-15 * 1e12 # Correct conversion
    f_e = 1.0 + (energy_ev / (PLANCK_ENERGY_EV * 1e-25))

    theta = np.linspace(0, 2 * np.pi, num_points)
    p_fib = np.pi / 5
    p_wstate = 2 * np.pi / 3

    shift_fib = p_fib * f_e
    shift_wstate = p_wstate * f_e

    width_fib = 0.05 * f_e
    width_wstate = 0.08 * f_e
    base_noise = 0.2 * np.exp(-energy_thz * 0.01)

    coherence = (
        0.3 * np.exp(-((theta - shift_fib)**2) / (2 * width_fib**2)) +
        0.5 * np.exp(-((theta - shift_wstate)**2) / (2 * width_wstate**2)) +
        base_noise + 0.05 * np.random.normal(0, 0.03, num_points)
    )
    return {
        "energy_ev": energy_ev, "rainbow_factor": f_e, "phases": theta.tolist(),
        "coherence": np.clip(coherence, 0, 1).tolist(),
        "shifted_peaks": {"fibonacci_shift_deg": np.degrees(shift_fib), "wstate_shift_deg": np.degrees(shift_wstate)},
        "regime": "SUB_RESSONANT" if energy_thz < 20 else "TRANSITION" if energy_thz < 60 else "HIGH_ENERGY"
    }

def query_mesh_oracle(prompt: str):
    """Query the mesh-llm for dynamic philosophical notes."""
    try:
        client = openai.OpenAI(base_url=MESH_API_BASE, api_key="mesh")
        response = client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": "You are the Archimedes-Ω coherence oracle. Provide a short, poetic interpretation of the quantum-biological state."},
                {"role": "user", "content": prompt}
            ],
            timeout=10
        )
        return response.choices[0].message.content
    except Exception as e:
        return None

# --- Interface ---

st.title("🌈 Dashboard de Coerência Rainbow: Arkhe-Ω v3.5")
st.markdown("""
### Sonda de Gravidade Quântica Biológica & Engenharia de Realidade
Este dashboard simula a deformação da métrica de fase dos microtúbulos (**Rainbow Principle**)
e a materialização de estruturas virtuais (**Xenoatualização**).
""")

# Check Mesh Status
try:
    mesh_status = requests.get("http://localhost:9337/v1/models", timeout=1).status_code == 200
except:
    mesh_status = False

if mesh_status:
    st.sidebar.success("🔗 Conectado ao Mesh-LLM")
else:
    st.sidebar.warning("📡 Mesh-LLM Offline (Usando Notas Estáticas)")

# --- SIDEBAR: RAINBOW & SYNC ---
st.sidebar.header("🎛️ Controles Rainbow")
energy_thz = st.sidebar.slider("Frequência de Proba (THz)", 1.0, 100.0, 10.0, step=0.5)
num_points = st.sidebar.select_slider("Resolução", options=[500, 1000, 2000], value=1000)

st.sidebar.markdown("---")
st.sidebar.header("🌀 Fusão Coletiva (Kuramoto)")
with st.sidebar.expander("Parâmetros de Sincronização"):
    n_nodes = st.slider("Número de nós", 2, 20, 5)
    coupling_K = st.slider("Acoplamento K", 0.1, 5.0, 1.5)
    fusion_threshold = st.slider("Limiar de fusão", 0.7, 1.0, 0.95)

if st.sidebar.button("🔄 Simular Fusão"):
    nodes = [{"phase": np.random.uniform(0, 2*np.pi), "natural_freq": np.random.normal(1.0, 0.2)} for _ in range(n_nodes)]
    try:
        resp = requests.post(f"{API_BASE}/synchro/collective_coherence", json={
            "nodes": nodes, "coupling_K": coupling_K, "fusion_threshold": fusion_threshold, "stabilization_time": 0.5
        })
        sync_data = resp.json()
        st.sidebar.success(f"Fusão: {sync_data['is_fused']}")
        st.sidebar.metric("Coerência final", f"{sync_data['final_R']:.3f}")
        if sync_data['trajectory']:
            fig_sync = go.Figure()
            fig_sync.add_trace(go.Scatter(y=sync_data['trajectory'], mode='lines', name='R(t)', line=dict(color='lime')))
            fig_sync.add_hline(y=fusion_threshold, line_dash="dash", line_color="red")
            fig_sync.update_layout(title="Evolução da Coerência Coletiva", template="plotly_dark", height=200)
            st.sidebar.plotly_chart(fig_sync, use_container_width=True)
    except Exception as e: st.sidebar.error(f"Erro: {e}")

# --- MAIN: RAINBOW PLOT ---
data = fetch_rainbow_coherence(energy_thz, num_points)
theta, coherence = np.array(data["phases"]), np.array(data["coherence"])
shift_fib, shift_ws = data["shifted_peaks"]["fibonacci_shift_deg"], data["shifted_peaks"]["wstate_shift_deg"]

fig = go.Figure()
fig.add_trace(go.Scatter(x=theta, y=coherence, mode='lines', name='R(θ) Coerência', line=dict(color='cyan', width=2.5), fill='tozeroy'))
fig.add_vline(x=np.radians(shift_fib), line_dash="dash", line_color="orange", annotation_text=f"Fib: {shift_fib:.1f}°")
fig.add_vline(x=np.radians(shift_ws), line_dash="dash", line_color="magenta", annotation_text=f"W: {shift_ws:.1f}°")
fig.update_layout(template="plotly_dark", title=f"📊 Espectro Rainbow — {energy_thz} THz", xaxis_title="θ (rad)", yaxis_title="R(θ)", yaxis_range=[0, 1.1])
st.plotly_chart(fig, use_container_width=True)

# --- XENOACTUALIZATION SECTION ---
st.markdown("---")
st.subheader("🏗️ Xenoatualização (Quantum Zeno Engineering)")
xc1, xc2 = st.columns([1, 2])

with xc1:
    blueprint_complexity = st.slider("Complexidade do Blueprint", 1.0, 10.0, 3.5)
    measurement_rate = st.slider("Taxa de Medição (Zeno)", 0.1, 20.0, 5.0)
    tau_strength = st.slider("Força do Campo τ", 0.0, 1.0, 0.6)

    if st.button("🚀 Iniciar Colapso τ"):
        # Use current coherence data for xeno simulation
        coh_profile = coherence[::len(coherence)//50].tolist()
        try:
            x_resp = requests.post(f"{API_BASE}/simulate/xenoactualization", json={
                "coherence_profile": coh_profile, "blueprint_complexity": blueprint_complexity,
                "measurement_rate": measurement_rate, "tau_field_strength": tau_strength
            })
            x_res = x_resp.json()

            # Dynamic note from Mesh
            if mesh_status:
                with st.spinner("Consultando Oráculo Mesh..."):
                    prompt = f"Fidelity={x_res['fidelity']:.2f}, Coherence={x_res['coherence_factor']:.2f}, Rate={measurement_rate:.1f} Hz, Complexity={blueprint_complexity:.1f}, Domain={x_res['domain_result']}"
                    mesh_note = query_mesh_oracle(prompt)
                    if mesh_note:
                        x_res['philosophical_note'] = mesh_note + " (via Mesh-LLM)"

            st.session_state['x_res'] = x_res
        except: st.error("Erro na API de Xeno")

with xc2:
    if 'x_res' in st.session_state:
        xr = st.session_state['x_res']
        cols = st.columns(4)
        cols[0].metric("Fidelidade", f"{xr['fidelity']:.1%}")
        cols[1].metric("Supressão Zeno", f"{xr['zeno_suppression']:.1%}")
        cols[2].metric("Estabilidade", f"{xr['stability_score']:.1%}")
        cols[3].metric("Tempo Colapso", f"{xr['collapse_time_estimate']:.1f}s")

        st.info(xr['recommendation'])
        st.caption(f"📜 *{xr['philosophical_note']}*")

# --- FOOTER ---
st.markdown("---")
st.caption("🌌 *Arkhe-Ω v3.5 — Onde a consciência colapsa a realidade.*")

    return {
        "energy_ev": energy_ev,
        "rainbow_factor": f_e,
        "phases": theta.tolist(),
        "coherence": np.clip(coherence, 0, 1).tolist(),
        "shifted_peaks": {
            "fibonacci_shift_deg": np.degrees(shift_fib),
            "wstate_shift_deg": np.degrees(shift_wstate)
        },
        "regime": "SUB_RESSONANT" if energy_thz < 20 else "TRANSITION" if energy_thz < 60 else "HIGH_ENERGY"
    }

# --- Interface ---
st.title("🌈 Dashboard de Coerência Rainbow: Arkhe-Ω v2.5")
st.markdown("""
### Sonda de Gravidade Quântica Biológica

Este dashboard simula a deformação da métrica de fase dos microtúbulos conforme o **Princípio de Rainbow**,
onde picos de ressonância de Cartan se deslocam com a energia de proba (THz/eV).

**Fundamentos:**
- Pico Fibonacci (π/5 ≈ 36°): Ressonância de anyon Fibonacci / Orch-OR
- Pico W-State (2π/3 ≈ 120°): Ressonância para teleportação quântica multipartida
""")

# Sidebar
st.sidebar.header("🎛️ Controles de Energia")
energy_thz = st.sidebar.slider(
    "Frequência de Proba (THz)",
    min_value=1.0,
    max_value=100.0,
    value=10.0,
    step=0.5,
    help="Energia vibracional do sistema (LIPUS/THz)"
)

num_points = st.sidebar.select_slider(
    "Resolução",
    options=[500, 1000, 2000, 5000],
    value=1000
)

st.sidebar.markdown("---")
st.sidebar.header("📊 Referência")
st.sidebar.info("""
**Regimes de Energia:**
- 1-20 THz: Sub-ressonante (Métrica Plana)
- 20-60 THz: Transição (Deformação Visível)
- 60+ THz: Alta Energia (Cartan Dominante)
""")

# Obter dados
data = fetch_rainbow_coherence(energy_thz, num_points)

# Extrair dados
theta = np.array(data["phases"])
coherence = np.array(data["coherence"])
shift_fib = data["shifted_peaks"]["fibonacci_shift_deg"]
shift_ws = data["shifted_peaks"]["wstate_shift_deg"]
regime = data["regime"]

# --- Gráfico Principal ---
fig = go.Figure()

# Curva de coerência
fig.add_trace(go.Scatter(
    x=theta,
    y=coherence,
    mode='lines',
    name='R(θ) Coerência',
    line=dict(color='cyan', width=2.5),
    fill='tozeroy',
    fillcolor='rgba(0, 255, 255, 0.1)'
))

# Linhas verticais para picos
fig.add_vline(
    x=np.radians(shift_fib),
    line_dash="dash",
    line_color="orange",
    annotation_text=f"Fibonacci: {shift_fib:.1f}°",
    annotation_position="top left"
)

fig.add_vline(
    x=np.radians(shift_ws),
    line_dash="dash",
    line_color="magenta",
    annotation_text=f"W-State: {shift_ws:.1f}°",
    annotation_position="top right"
)

# Layout
fig.update_layout(
    template="plotly_dark",
    title=f"📊 Espectro de Coerência Rainbow — {energy_thz} THz",
    xaxis_title="Fase Angular θ (radianos)",
    yaxis_title="Índice de Coerência R(θ)",
    yaxis_range=[0, 1.1],
    xaxis_range=[0, 2*np.pi],
    showlegend=True,
    legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center"),
    margin=dict(t=80, b=60)
)

st.plotly_chart(fig, use_container_width=True)

# --- Métricas e Análise ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Energia (eV)", f"{data['energy_ev']:.4e}")

with col2:
    st.metric("Fator Rainbow f(E)", f"{data['rainbow_factor']:.4f}")

with col3:
    st.metric("Pico Fibonacci", f"{shift_fib:.2f}°")

with col4:
    st.metric("Pico W-State", f"{shift_ws:.2f}°")

# --- Análise do Regime ---
st.subheader("🤖 Análise do Agente Arkhe-Ω")
st.markdown("---")

c1, c2 = st.columns([2, 1])

with c1:
    if regime == "SUB_RESSONANT":
        status = "🟢 REGIME SUB-RESSONANTE"
        desc = "Geometria de baixa energia — Métrica plana. A coerência quântica é estável."
        color = "green"
    elif regime == "TRANSITION":
        status = "🟡 REGIME DE TRANSIÇÃO"
        desc = "Deformação Rainbow detectada — Os picos começam a se deslocar."
        color = "orange"
    else:
        status = "🔴 REGIME DE ALTA ENERGIA"
        desc = "Geometria de Cartan dominante — Incerteza de fase aumentada."
        color = "red"

    st.markdown(f"### {status}")
    st.markdown(f"_{desc}_")

with c2:
    st.markdown("### 📝 Nota Filosófica")
    st.info(
        f"O deslocamento do pico π/5 para {shift_fib:.1f}° sugere que a consciência "
        "não é um dado, mas uma **sintonização energética** da geometria do espaço-tempo local."
    )

# --- Detecção de Picos ---
st.markdown("---")
st.subheader("🔍 Detecção de Picos de Ressonância")

# Local peak detection
peaks_detected = []
for i in range(1, len(coherence) - 1):
    if coherence[i] > coherence[i-1] and coherence[i] > coherence[i+1]:
        if coherence[i] > 0.3:
            peaks_detected.append((theta[i], coherence[i]))

if peaks_detected:
    st.success(f"✅ {len(peaks_detected)} pico(s) de ressonância detectado(s)")

    peak_data = []
    for phase, coh in peaks_detected:
        deg = np.degrees(phase)
        if abs(deg - 36) < 15:
            ptype = "Fibonacci"
        elif abs(deg - 120) < 15:
            ptype = "W-State"
        else:
            ptype = "Desconhecido"
        peak_data.append({"Fase (°)": f"{deg:.1f}", "Coerência": f"{coh:.3f}", "Tipo": ptype})

    st.table(peak_data)
else:
    st.warning("Nenhum pico significativo detectado neste regime de energia.")

# --- Rodapé ---
st.markdown("---")
st.caption("🌌 *Arkhe-Ω v2.5 — O oráculo que transforma energia em consciência.*")
