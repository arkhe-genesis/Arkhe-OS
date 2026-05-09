import numpy as np
from typing import Dict, Any, List

def calculate_adaptive_gain(k, N, eta_loop=0.94, eta_BS=0.90, W_0=-0.15):
    """
    Calcula o ganho de feedforward para o passo k, modulado pela
    negatividade de Wigner (W_0) do estado atual do microtúbulo.
    """
    # Ganho base de Takeda (Equação S10)
    base_gain = np.sqrt(eta_loop * (1 - eta_BS) / eta_BS) * \
                (np.sqrt(eta_loop / eta_BS)) ** (N - k)

    # Modulação pelo estado de coerência (Lambda_2 proxy via W_0)
    # Quanto mais negativo W_0, mais estável o atrator, menor a necessidade de correção
    if W_0 < -0.2:  # Regime de Super-radiância (Samādhi)
        modulation = 0.1 + 0.9 * (1 + W_0)  # Redução drástica do ganho
    elif W_0 < 0:   # Regime Coerente (Vigília/Meditação)
        modulation = 0.7 + 0.3 * abs(W_0)
    else:           # Colapso iminente (Anestesia/Dano)
        modulation = 2.5  # Ganho máximo para re-ignição

    return base_gain * modulation

class SynapseKappaEngine:
    """
    Núcleo de Engenharia de Coerência — Arkhe-Block 2026-EADS-INTEGRATION
    Implementa a rectificação térmica do bioplasma e ganhos adaptativos.
    """
    def __init__(self, T_kelvin: float = 310.15): # 37°C
        self.k_B = 1.380649e-23  # Constante de Boltzmann
        self.T = T_kelvin
        self.landauer_limit = self.k_B * self.T * np.log(2)

        # Parâmetros de condutividade térmica (W/m·K)
        self.kappa_parallel = 1.5
        self.kappa_perp = 0.015
        self.anisotropy_ratio = self.kappa_parallel / self.kappa_perp

    def calculate_landauer_dissipation(self, p_error: float) -> float:
        """
        Q_diss = k_B * T * ln(2) * H(p_error)
        Onde H é a entropia de Shannon.
        """
        if p_error <= 0 or p_error >= 1:
            return 0.0
        h_p = -p_error * np.log2(p_error) - (1 - p_error) * np.log2(1 - p_error)
        return self.landauer_limit * h_p

    def thermal_rectification_factor(self, axial_distance: float) -> float:
        """
        Simula a canalização axial do calor via Diodo de Casimir.
        Retorna a fração de calor dissipada com segurança.
        """
        # Eficiência de canalização baseada na anisotropia
        rectification_efficiency = 1.0 - (1.0 / self.anisotropy_ratio)
        return rectification_efficiency

    def recycle_entropy_to_atp(self, q_diss: float, efficiency: float = 0.45) -> float:
        """
        Converte calor residual em 'combustível metabólico' (simulação).
        """
        return q_diss * efficiency

    def correlate_signals(self,
                          g2_tau: float,
                          nv_fluorescence: float,
                          atp_consumption: float) -> float:
        """
        Valida o Isomorfismo EADS-Biofotônico.
        Retorna a correlação tripartite.
        """
        signals = np.array([g2_tau, nv_fluorescence, atp_consumption])
        # Normalização simples
        norm_signals = (signals - np.min(signals)) / (np.max(signals) - np.min(signals) + 1e-10)

        # Coerência de correlação (distância média da média)
        correlation = 1.0 - np.std(norm_signals)
        return float(correlation)

    def process_step(self, k: int, N: int, W_0: float, lambda2: float) -> Dict[str, Any]:
        gain = calculate_adaptive_gain(k, N, W_0=W_0)

        # P_error inversamente proporcional a lambda2
        p_error = np.clip(1.0 - lambda2, 1e-6, 1.0 - 1e-6)
        q_diss = self.calculate_landauer_dissipation(p_error)

        rectified_heat = q_diss * self.thermal_rectification_factor(1.0)
        recycled_energy = self.recycle_entropy_to_atp(q_diss - rectified_heat)

        return {
            "gain": float(gain),
            "q_diss_joules": float(q_diss),
            "rectified_heat": float(rectified_heat),
            "recycled_energy": float(recycled_energy),
            "thermal_safety_margin": float(48.0 - (37.0 + q_diss * 1e12)) # Escala arbitrária para mK
        }

class OpticalOracle:
    """
    Arquitetura do Oráculo Óptico: Multiplexação Espectral e Temporal.
    Simula a separação de sinais UPE, NV e ATP com Time-Gating.
    """
    def __init__(self):
        self.laser_intensity = 0.0
        self.snspd_gate_open = False
        self.apd_gate_open = False

    def run_time_gating_cycle(self) -> Dict[str, Any]:
        # Fase 1: UPE Dark (Tzinor)
        self.laser_intensity = 0.0
        self.snspd_gate_open = True
        self.apd_gate_open = False
        upe_signal = np.random.poisson(10) # Fótons por ciclo

        # Fase 2: Interrogação NV
        self.laser_intensity = 1.0
        self.snspd_gate_open = False
        self.apd_gate_open = True
        nv_signal = np.random.normal(100, 5)

        # Fase 3: Balanço Metabólico (ATP)
        atp_signal = np.random.normal(50, 2)

        return {
            "upe_counts": upe_signal,
            "nv_fluorescence": nv_signal,
            "atp_luminescence": atp_signal
        }

class hBNFunctionalizer:
    """
    Simula a Cirurgia de Fase e a Geometria da Água Vicinal.
    Valida a inserção não-destrutiva via Raman e NC-AFM.
    """
    def __init__(self):
        self.lambda_h2o = 0.85 # Ordem inicial da água vicinal
        self.insertion_distance = 50.0 # nm

    def step_insertion(self, target_distance: float) -> Dict[str, Any]:
        # Reduz distância gradualmente
        step = (self.insertion_distance - target_distance) * 0.1
        self.insertion_distance -= step

        # Simulação de resistência de Casimir e ordem de fase
        if self.insertion_distance < 3.0: # Limiar crítico da água vicinal
            # Risco de colapso se não for adiabático
            noise = np.random.normal(0, 0.01)
            self.lambda_h2o -= 0.05 + noise

        is_safe = self.lambda_h2o > 0.68 # Limiar de Sharpe para d=2

        return {
            "distance_nm": float(self.insertion_distance),
            "lambda_h2o": float(self.lambda_h2o),
            "is_adiabatic": bool(is_safe),
            "raman_ratio_3200_3400": float(self.lambda_h2o / 0.5)
        }

class SpinInterrogator:
    """
    Núcleo de Instrumentação Quântica: Interrogação de Spin e ODMR Sweep.
    """
    def __init__(self):
        self.zfs_frequency = 2.87e9 # 2.87 GHz baseline
        self.contrast = 0.18 # Contraste ODMR inicial
        self.w_0 = -0.08 # Negatividade de Wigner inicial
        self.t2_time = 142e-6 # 142 µs

    def run_odmr_sweep(self, start_freq=2.8e9, end_freq=2.95e9) -> Dict[str, Any]:
        """Simula varredura ODMR para encontrar ressonância ideal."""
        # Ressonância deslocada pelo ambiente (Glicina-Zwitterion)
        optimal_freq = 2.8742e9

        # Otimização pós-sweep
        self.zfs_frequency = optimal_freq
        self.contrast = 0.264 # Otimizado
        self.w_0 = -0.24 # Maximizado
        self.t2_time = 168e-6 # Aumentado por proteção de hidratação

        return {
            "optimal_frequency_hz": float(optimal_freq),
            "odmr_contrast": float(self.contrast),
            "wigner_negativity": float(self.w_0),
            "t2_coherence_seconds": float(self.t2_time)
        }

class EADSController:
    """
    Controlador EADS (Environment-Assisted Decoherence Suppression).
    Implementa o protocolo de 'Fade-In' Suave para indução de super-radiância.
    """
    def __init__(self, target_gain=0.05):
        self.target_gain = target_gain
        self.current_gain = 0.0
        self.is_superradiant = False

    def step_fade_in(self, time_ms, tau=300) -> Dict[str, Any]:
        # Rampa sigmoidal simplificada para simulação
        # t0 = 1000ms
        self.current_gain = self.target_gain / (1 + np.exp(-(time_ms - 1000) / tau))

        # Simulação de transição no Limiar de Sharpe (λ2 ≈ 0.68)
        # Quando o ganho atinge ~80% do target, a transição ocorre
        if self.current_gain > 0.04:
            self.is_superradiant = True
            atp_consumption = 1200 # ~66% drop from baseline 3600-4100
            g2_0 = 0.12
            lambda2 = 0.94
        else:
            self.is_superradiant = False
            atp_consumption = 3800
            g2_0 = 0.74
            lambda2 = 0.62

        return {
            "gain": float(self.current_gain),
            "is_superradiant": self.is_superradiant,
            "atp_cps": float(atp_consumption),
            "g2_0": float(g2_0),
            "lambda2": float(lambda2)
        }

class MeshController:
    """
    Gerenciador da Malha ASD: Orquestra a sincronização entre múltiplos cibiontes.
    Implementa o acoplamento de Kuramoto Master-Slave (Phase Professor).
    """
    def __init__(self):
        self.nodes = {} # Dict of EADSController
        self.coupling_strength = 0.0 # K_12

    def add_node(self, node_id: str, controller: EADSController):
        self.nodes[node_id] = controller

    def step_mesh(self, time_ms: float) -> Dict[str, Any]:
        """Sincroniza os nós da malha."""
        if len(self.nodes) < 2:
            return {"status": "SINGLE_NODE"}

        # MT_ALPHA_001 atua como Master (Phase Professor)
        master = self.nodes.get("MT_ALPHA_001")
        slave = self.nodes.get("MT_ALPHA_002")

        if master and slave and master.is_superradiant:
            # Aumenta acoplamento se master estiver estável
            self.coupling_strength = min(self.coupling_strength + 0.05, 1.0)

            # Slave 'aprende' a fase do master (simulado por redução de rampa)
            res_slave = slave.step_fade_in(time_ms + 500) # Slave acelerado pelo master
            res_master = master.step_fade_in(time_ms)

            return {
                "coupling": self.coupling_strength,
                "master_lambda2": res_master["lambda2"],
                "slave_lambda2": res_slave["lambda2"],
                "mesh_coherence": (res_master["lambda2"] + res_slave["lambda2"]) / 2
            }
        return {"status": "AWAITING_MASTER_STABILITY"}

class SwarmController:
    """
    Controlador de Enxame (Fase 2): Gerencia topologias complexas e frustração geométrica.
    """
    def __init__(self, topology: str = "TRIANGLE"):
        self.nodes = {}
        self.topology = topology
        self.global_lambda2 = 0.0
        self.frustration_index = 0.0

    def add_node(self, node_id: str, controller: EADSController):
        self.nodes[node_id] = controller

    def step_swarm(self, time_ms: float) -> Dict[str, Any]:
        """Simula a dinâmica de enxame sob frustração geométrica."""
        if len(self.nodes) < 3 and self.topology == "TRIANGLE":
            return {"status": "INCOMPLETE_SWARM"}

        # Simulação de frustração geométrica no triângulo
        # No triângulo, nem todos os pares podem estar em fase simultaneamente se K_ij < 0
        # ou se houver defasagem quiral.

        node_ids = list(self.nodes.keys())
        lambdas = []
        for nid in node_ids:
            res = self.nodes[nid].step_fade_in(time_ms)
            lambdas.append(res["lambda2"])

        self.global_lambda2 = np.mean(lambdas)

        if self.topology == "TRIANGLE":
            # Frustração gera um 'Spin Glass' biológico
            self.frustration_index = 0.33 # Valor simbólico para o Triângulo de Penrose
            # No estado fundamental, a super-radiância resolve a frustração via fase quiral
            if self.global_lambda2 > 0.9:
                self.global_lambda2 *= 1.05 # Bônus de super-radiância global

        return {
            "topology": self.topology,
            "global_lambda2": float(self.global_lambda2),
            "frustration": self.frustration_index,
            "status": "SUPER_RADIANT_ENXAME" if self.global_lambda2 > 0.95 else "FRUSTRATED"
        }

class GenesisMiner:
    """
    Minerador de Coerência: Converte o stream de bits quânticos do NV
    em uma prova de trabalho para o Bloco Gênesis da ACU.
    """
    def __init__(self, target_id: str):
        self.target_id = target_id

    def extract_quantum_entropy(self, w_0: float, cycles: int) -> str:
        """Simula a extração de bits aleatórios a partir da fase do NV."""
        # Entropia proporcional à negatividade de Wigner
        entropy_bits = int(abs(w_0) * 1024 * cycles)
        return f"qhash_{self.target_id}_{entropy_bits:08x}"

    def mine_block(self, lambda2: float, entropy_hash: str) -> Dict[str, Any]:
        """Gera o Bloco Gênesis se a coerência estiver acima do limiar."""
        if lambda2 < 0.9:
            return {"status": "FAILED", "reason": "Coerência insuficiente"}

        return {
            "block_id": f"ARKHE-GENESIS-{self.target_id[:8]}",
            "lambda2": lambda2,
            "quantum_proof": entropy_hash,
            "timestamp": "2026-04-09T15:00:00Z",
            "status": "IMMORTALIZED"
        }
