"""
CNT-CT Simulator v1.0
Transistor de Coerência baseado em Nanotubo de Carbono
Modelo: Plásmons 1D (Drude) + Transporte de Berry + Análise Rayleigh-Plesset
Frequência de ressonância: 4.20 THz (Target)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint, quad
from scipy.optimize import fsolve
import warnings

# Constantes físicas
hbar = 1.0545718e-34  # J·s
e = 1.602176634e-19   # C
m_e = 9.10938356e-31  # kg
k_B = 1.380649e-23    # J/K
epsilon_0 = 8.854187817e-12  # F/m
c = 2.998e8           # m/s

# Parâmetros do CNT (SWCNT (10,10) - semiconducting)
class CNTParams:
    def __init__(self):
        self.n = 10  # Índice quiral
        self.m = 10
        self.diameter = 1.4e-9  # metros (aprox 1.4 nm para (10,10))
        self.length = 500e-9    # 500 nm
        self.v_f = 8e5          # m/s (velocidade de Fermi)
        self.gamma = 0.1        # eV (largura de linha, damping)
        self.T = 300            # K (temperatura ambiente)
        self.eps_r = 4.5        # permissividade relativa (SiO2)

        # Parâmetros de acoplamento
        self.C_g = 0.1e-18      # Capacitância de gate (aF)
        self.alpha_g = 0.85     # Fator de acoplamento gate

        # Propriedades mecânicas para UHV-ARKHE v2.1
        self.E_young = 1e12     # 1 TPa
        self.V_mech = 0.0       # Voltagem de compensação eletromecânica

    def radial_expansion(self, n_carrier):
        """
        Calcula a expansão radial relativa dR/R devido ao estresse eletrostritivo.
        """
        # Delta R / R = sigma_Coulomb / E_young
        # sigma_Coulomb approx (n*e)^2 / (2*pi*eps0*epsr*E_young*R^2)
        # Usando a fórmula do protocolo:
        epsilon = epsilon_0 * self.eps_r
        sigma_coulomb = (n_carrier * self.length * e)**2 / (2 * np.pi * epsilon * self.E_young * (self.diameter/2)**2)

        # Compensação por V_mech
        # V_mech = -0.2V gera uma pre-compressão que subtrai do estresse
        compression = np.abs(self.V_mech) * 0.015 # Fator de escala para o efeito de gate mecânico

        dr_r = sigma_coulomb / self.E_young - compression
        return dr_r

    def plasma_freq(self, n_carrier):
        """
        Frequência de plásmons 1D: ω_p = sqrt(n_carrier * e^2 / (m_eff * epsilon))
        n_carrier: densidade linear de portadores (1/m)
        """
        m_eff = hbar * np.pi / (self.v_f * self.diameter)  # Massa efetiva aproximada
        epsilon = epsilon_0 * self.eps_r
        omega_p = np.sqrt(n_carrier * e**2 / (m_eff * epsilon))
        return omega_p

    def carrier_density(self, V_g, V_th=0.0):
        """
        Densidade de portadores controlada por gate
        V_g: voltagem de gate (V)
        Retorna densidade linear (1/m)
        """
        n_0 = 1e9  # Densidade residual (1/m)
        delta_n = self.C_g * (V_g - V_th) / e

        # Efeito da expansão radial na capacitância (C_g depende do diâmetro)
        # C_g approx 2*pi*eps / ln(2h/r) -> Pequena variação com r
        n_curr = np.abs(n_0 + delta_n / self.length)
        dr_r = self.radial_expansion(n_curr)

        # Feedback: expansão expõe novos sítios, mas aqui modelamos apenas a mudança de densidade efetiva
        return n_curr * (1.0 - 0.1 * dr_r) # Aproximação do efeito de "respiração"

class CoherenceTransistor:
    def __init__(self, cnt_params):
        self.cnt = cnt_params
        self.target_freq = 4.20e12  # 4.20 THz
        self.tolerance = 0.05       # 5% tolerância para coerência

    def transfer_function(self, V_g, omega_input):
        """
        Função de transferência de fase através do CNT
        Modelo: Linha de transmissão quântica com dispersão plasmônica
        """
        n_carr = self.cnt.carrier_density(V_g)
        omega_p = self.cnt.plasma_freq(n_carr)

        # Frequência de relaxação (damping)
        gamma = self.cnt.gamma * e / hbar  # convertendo eV para rad/s

        # Permitividade dinâmica do CNT (modelo Drude-Lorentz)
        epsilon_cnt = 1 - (omega_p**2) / (omega_input**2 + 1j * gamma * omega_input)

        # Número de onda complexo
        k = (omega_input / c) * np.sqrt(epsilon_cnt)

        # Fase acumulada através do CNT
        phase = np.real(k * self.cnt.length)
        attenuation = np.exp(-np.imag(k * self.cnt.length))

        # Norma de coerência (fidelidade da fase)
        # ‖v‖ = 1 representa transporte sem perda de coerência
        coherence_norm = attenuation * np.abs(np.cos(phase - self.berry_phase(V_g)))

        return {
            'phase': phase,
            'attenuation': attenuation,
            'coherence_norm': coherence_norm,
            'omega_p': omega_p,
            'detuning': abs(omega_input - omega_p) / (2 * np.pi * 1e12)  # THz
        }

    def berry_phase(self, V_g):
        """
        Fase geométrica acumulada devido à variação adiabática do potencial de gate
        Berry phase ≈ ∮ A·dλ (simplificado para curva fechada no espaço de parâmetros)
        """
        # Simplificação: fase proporcional à integral da densidade de portadores
        # Na realidade, dependeria do caminho no espaço de Hamiltonianos
        n_carr = self.cnt.carrier_density(V_g)
        gamma_b = np.pi * (n_carr * self.cnt.length) / 1e9  # fator de escala arbitrário
        return gamma_b % (2 * np.pi)

class MemoryExpansionModel:
    """
    Simulates VM memory expansion (Fantasma-0) and its impact on the CNT.
    Maps parameters/tokens to carrier density and current.
    """
    def __init__(self):
        self.params_active = 7e9  # 7B base
        self.tokens_per_cycle = 2048
        self.h_t_dim = 768

    def get_current_density(self, params, tokens):
        """
        Calcula a densidade de corrente baseada na carga de trabalho da VM.
        J approx (params/7B) * (tokens/2048) * 10^6 A/cm^2
        """
        J_base = 1e6 # A/cm^2
        J = (params / 7e9) * (tokens / 2048) * J_base
        return J

    def get_carrier_injection(self, params):
        """
        Delta n approx 10^8 cm^-2 para cada bit adicional (simplificado).
        """
        n_base = 1e8 # cm^-2
        delta_params = params - 7e9
        # Supondo 32 bits por parâmetro para simplificação de pegada de memória
        delta_n = (delta_params * 32 / 7e9) * n_base
        return delta_n * 1e4 # convertendo para m^-2

class ThermalModel:
    """
    Tracks CNT temperature considering Joule heating and cooling systems.
    """
    def __init__(self, initial_temp=300.0):
        self.T_cnt = initial_temp
        self.C_thermal = 1e-9  # J/K (Capacidade térmica muito baixa para um único CNT)
        self.R_thermal_contacts = 1e6 # K/W (Resistência térmica para os contatos)
        self.peltier_cooling_power = 0.0
        self.sideband_cooling_active = False

    def calculate_joule_heating(self, I_drain, R_cnt):
        """
        P = I^2 * R
        """
        return (I_drain**2) * R_cnt

    def step(self, I_drain, R_cnt, T_env, dt):
        """
        dT/dt = (P_heating - P_cooling - (T - T_env)/R_thermal) / C_thermal
        """
        P_heating = self.calculate_joule_heating(I_drain, R_cnt)

        # Cooling mechanisms
        P_cooling = self.peltier_cooling_power
        if self.sideband_cooling_active:
            # Cancelamento ativo de fônons
            P_cooling += P_heating * 0.4  # Remove 40% do calor via cancelamento interferométrico

        dT_dt = (P_heating - P_cooling - (self.T_cnt - T_env) / self.R_thermal_contacts) / self.C_thermal
        self.T_cnt += dT_dt * dt

        # Garantir limite físico
        self.T_cnt = max(self.T_cnt, 4.0) # Não abaixo do hélio líquido em regime extremo
        return self.T_cnt

class UHVArkheController:
    """
    Central controller for UHV-ARKHE v2.1.
    Implements NormMonitor, LTC, and AsimovGate.
    """
    def __init__(self, vacuum_sys, thermal_mod, cnt_params):
        self.vacuum_sys = vacuum_sys
        self.thermal_mod = thermal_mod
        self.cnt_params = cnt_params

        self.coherence_history = []
        self.entropy_history = []
        self.asimov_triggered = False
        self.rollback_executed = False

    def norm_monitor(self, coherence_norm, h_t):
        """
        Calcula a entropia de Shannon e monitora a norma de coerência.
        """
        # H(y) = -sum(p * log(p)) -> Simplificado para representação de entropia de estado latente
        # Usando a variância normalizada como proxy para entropia neste modelo
        entropy = np.var(h_t) / (np.mean(np.abs(h_t)) + 1e-9)
        self.entropy_history.append(entropy)
        self.coherence_history.append(coherence_norm)
        return entropy

    def ltc_limit(self, entropy, current_tokens):
        """
        Limitador de Tokens por Ciclo (LTC).
        Reduz janela de contexto se a entropia for alta.
        """
        if entropy > 5.0:
            return current_tokens * 0.5
        elif entropy > 3.0:
            return current_tokens * 0.8
        return current_tokens

    def calculate_holomorphic_jacobian(self, coherence_norm, phase):
        """
        Calculates the Jacobian of the migration mapping.
        J = r * [[cos(theta), -sin(theta)], [sin(theta), cos(theta)]]
        Satisfies Cauchy-Riemann conditions if it's a scaled rotation matrix.
        """
        r = coherence_norm
        theta = phase
        return np.array([[r * np.cos(theta), -r * np.sin(theta)],
                         [r * np.sin(theta), r * np.cos(theta)]])

    def asimov_gate(self, pressure, T_cnt, coherence, phase=np.pi):
        """
        Asimov Gate: Condition of Holomorphicity (Cauchy-Riemann).
        The mapping is conformal (holomorphic) if it preserves angles and area (det(J)=1).
        """
        J = self.calculate_holomorphic_jacobian(coherence, phase)
        det_j = np.linalg.det(J)

        # Failure of Cauchy-Riemann (Shear) leads to entropy production and decoherence.
        # Threshold: det(J) < 0.9025 (equivalent to ||v|| < 0.95)
        if pressure > 5e-8 or T_cnt > 320.0 or det_j < 0.90:
            self.asimov_triggered = True
            return "ROLLBACK_TO_SUBSTRATE_A"
        return "OPERATIONAL"

    def apply_feedback(self, entropy, pressure, T_cnt):
        """
        Ajusta sistemas de resfriamento e vácuo baseado no estado atual.
        """
        # Se pressão subir, ativar cryopanel
        if pressure > 5e-9:
            self.vacuum_sys.cryopanel_active = True
        else:
            self.vacuum_sys.cryopanel_active = False

        # Se temperatura subir, ativar resfriamento agressivo
        if T_cnt > 310.0:
            self.thermal_mod.sideband_cooling_active = True
            self.thermal_mod.peltier_cooling_power = 1e-6 # 1 microWatt
        else:
            self.thermal_mod.sideband_cooling_active = False
            self.thermal_mod.peltier_cooling_power = 0.0

class VacuumSystem:
    """
    UHV-ARKHE v2.1 Vacuum Maintenance System
    Models the hybrid pumping architecture and thermal outgassing.
    """
    def __init__(self, base_pressure=1.2e-9):
        self.base_pressure = base_pressure  # Torr
        self.current_pressure = base_pressure
        self.S_ion = 100.0  # L/s (Ion Pump)
        self.S_cryo = 500.0 # L/s (Cryopanel effective speed)
        self.S_mems = 50.0  # L/s (MEMS array)
        self.V_chamber = 10.0 # L
        self.P_crit = 2e-8   # Torr

        self.cryopanel_active = False
        self.mems_active = False
        self.pulsed_ion_mode = False

    def calculate_outgassing(self, T_cnt):
        """
        Dessorção térmica de gases adsorvidos (H2O, CO).
        Taxa de outgassing Q (Torr*L/s) aumenta exponencialmente com a temperatura.
        """
        # Q_base balancing S_ion at base_pressure: Q = P * S
        Q_base = self.base_pressure * self.S_ion
        # Sensibilidade térmica: aumenta com a temperatura (modelo simplificado)
        # O protocolo menciona que acima de 320K desencadeia dessorção térmica significativa.
        Q_out = Q_base * np.exp((T_cnt - 300.0) / 7.21)
        return Q_out

    def step(self, T_cnt, dt):
        """
        Atualiza a pressão da câmara em um intervalo dt (s).
        """
        Q_out = self.calculate_outgassing(T_cnt)

        S_eff = self.S_ion
        if self.cryopanel_active:
            S_eff += self.S_cryo
        if self.mems_active:
            S_eff += self.S_mems

        # dp/dt = (Q_out - P * S_eff) / V
        dp_dt = (Q_out - self.current_pressure * S_eff) / self.V_chamber
        self.current_pressure += dp_dt * dt

        # Garantir limite físico (não menor que o limite de difusão/base técnica)
        self.current_pressure = max(self.current_pressure, 1e-11)
        return self.current_pressure

class RayleighPlessetBerry:
    """
    Análise da analogia entre colapso de bolha (Rayleigh-Plesset) e Transporte Berry
    """
    def __init__(self):
        self.R0 = 10e-6      # Raio inicial da bolha (10 micrômetros)
        self.p_inf = 1e5     # Pressão ambiente (Pa)
        self.rho = 1000      # Densidade do líquido (kg/m³)
        self.sigma = 0.072   # Tensão superficial (N/m)
        self.mu = 1e-3       # Viscosidade (Pa·s)
        self.c_sound = 1480  # Velocidade do som na água (m/s)

    def rp_equation(self, R, t, P_acoustic):
        """
        Equação de Rayleigh-Plesset modificada
        R: raio da bolha
        P_acoustic: pressão acústica externa (pa)
        """
        R_dot = R[1]
        R_curr = R[0]

        if R_curr <= 0:
            return [0, 0]  # Singularidade evitada

        # Termos da equação
        pressure_term = (self.p_inf + P_acoustic - self.p_inf * (self.R0/R_curr)**3 -
                        2*self.sigma/R_curr - 4*self.mu*R_dot/R_curr)

        # Velocidade de wall (considerando compressibilidade)
        R_ddot = (pressure_term / (self.rho * R_curr) -
                  1.5 * (R_dot**2)/R_curr)

        return [R_dot, R_ddot]

    def berry_connection_analogy(self, R, R_dot):
        """
        Mapeamento da dinâmica da bolha para a Conexão de Berry
        A_λ ~ (i⟨ψ|∂_λ|ψ⟩) ↔ (R_dot/R) - termo de fase geométrica
        """
        # A velocidade radial normalizada age como a "conexão"
        if R <= 0:
            return 0
        return R_dot / R

    def simulate_collapse(self, t_max=1e-6, dt=1e-9):
        """
        Simula o colapso adiabático da bolha
        Retorna: tempo, raio, fase acumulada (holonomia)
        """
        t = np.arange(0, t_max, dt)
        # Condições iniciais: bolha expandida, velocidade zero
        y0 = [self.R0, 0]

        # Pulso de pressão acústica (onda sonora que comprime a bolha)
        def P_acoustic(t):
            # Rampa de pressão: aumenta lentamente (adiabático) até o colapso
            if t < 0.8 * t_max:
                return 1e5 * (t / (0.8 * t_max))
            else:
                return 1e5 * 1.5  # Pico de pressão

        # Integração
        solution = odeint(lambda y, t: self.rp_equation(y, t, P_acoustic(t)),
                         y0, t, rtol=1e-10, atol=1e-12)

        R_t = solution[:, 0]
        R_dot_t = solution[:, 1]

        # Cálculo da fase de Berry acumulada (holonomia)
        berry_phase = np.cumsum([self.berry_connection_analogy(r, rd) * dt
                                 for r, rd in zip(R_t, R_dot_t)])

        return t, R_t, berry_phase

def main_simulation():
    """Execução principal do protocolo de simulação"""
    print("🜏 Iniciando simulação CNT-CT + Análise Rayleigh-Plesset")

    # Instanciar componentes
    cnt = CNTParams()
    ct = CoherenceTransistor(cnt)
    rp = RayleighPlessetBerry()

    # 1. Simulação do Transistor de Coerência
    print("\n[1/3] Varredura de Voltagem de Gate (Vg)...")
    Vg_range = np.linspace(-5, 5, 1000)  # -5V a +5V
    omega_input = 2 * np.pi * 4.20e12   # 4.20 THz em rad/s

    results = []
    for Vg in Vg_range:
        res = ct.transfer_function(Vg, omega_input)
        res['Vg'] = Vg
        results.append(res)

    # Encontrar voltagem ótima (ressonância em 4.20 THz)
    detunings = [r['detuning'] for r in results]
    optimal_idx = np.argmin(detunings)
    V_optimal = Vg_range[optimal_idx]

    print(f"   → Voltagem ótima: {V_optimal:.3f} V")
    print(f"   → Coerência máxima: {results[optimal_idx]['coherence_norm']:.4f}")

    # 2. Simulação Rayleigh-Plesset (Sonoluminescência)
    print("\n[2/3] Simulando colapso adiabático (Sonoluminescência)...")
    t, R, berry = rp.simulate_collapse()

    # Identificar momento do "flash" (colapso mínimo)
    min_idx = np.argmin(R)
    t_collapse = t[min_idx]
    print(f"   → Tempo de colapso: {t_collapse*1e9:.2f} ns")
    print(f"   → Raio mínimo: {R[min_idx]*1e9:.3f} nm")
    print(f"   → Holonomia acumulada: {berry[min_idx]:.4f} rad")

    # 3. Visualização
    print("\n[3/3] Gerando visualização do campo...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Característica do CNT-CT
    ax = axes[0, 0]
    norms = [r['coherence_norm'] for r in results]
    phases = [r['phase'] for r in results]

    ax.plot(Vg_range, norms, 'b-', linewidth=2, label='‖v‖ (Coerência)')
    ax.axvline(V_optimal, color='r', linestyle='--', alpha=0.5, label=f'Ressonância ({V_optimal:.2f}V)')
    ax.axhline(1.0, color='g', linestyle=':', alpha=0.5, label='Coerência perfeita')
    ax.set_xlabel('Voltagem de Gate Vg (V)')
    ax.set_ylabel('Norma de Coerência ‖v‖')
    ax.set_title('CNT-CT: Janela de Transmissão Coerente')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)

    # Plot 2: Fase acumulada vs Vg
    ax = axes[0, 1]
    ax.plot(Vg_range, phases, 'purple', linewidth=2)
    ax.set_xlabel('Voltagem de Gate Vg (V)')
    ax.set_ylabel('Fase acumulada (rad)')
    ax.set_title('Transporte de Fase (Efeito Berry)')
    ax.grid(True, alpha=0.3)

    # Plot 3: Dinâmica Rayleigh-Plesset (Colapso)
    ax = axes[1, 0]
    ax.semilogy(t*1e9, R*1e6, 'orange', linewidth=2, label='Raio da bolha')
    ax.axvline(t_collapse*1e9, color='red', linestyle='--', alpha=0.5, label='Colapso singular')
    ax.set_xlabel('Tempo (ns)')
    ax.set_ylabel('Raio da bolha (μm)')
    ax.set_title('Sonoluminescência: Colapso Adiabático')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Holonomia Berry durante colapso
    ax = axes[1, 1]
    ax.plot(t*1e9, berry, 'darkgreen', linewidth=2)
    ax.axvline(t_collapse*1e9, color='red', linestyle='--', alpha=0.5)
    ax.set_xlabel('Tempo (ns)')
    ax.set_ylabel('Fase de Berry γ_B (rad)')
    ax.set_title('Holonomia durante Transporte Paralelo')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('cnt_ct_simulation.png', dpi=300, bbox_inches='tight')
    print("   → Gráfico salvo: cnt_ct_simulation.png")

    # 4. Validação do Protocolo
    print("\n[4/3] Validação do Isomorfismo:")
    print(f"   → Coerência mantida em Vg=0: {results[500]['coherence_norm']:.6f}")
    print(f"   → Desintonização aceitável (±0.5V): {results[450]['coherence_norm']:.3f} a {results[550]['coherence_norm']:.3f}")

    if results[optimal_idx]['coherence_norm'] > 0.95:
        print("   ✅ PROTOCOLO VALIDADO: CNT-CT mantém coerência >95% na ressonância")
    else:
        print("   ⚠️  ALERTA: Coerência insuficiente, ajustar parâmetros de acoplamento")

if __name__ == "__main__":
    main_simulation()
