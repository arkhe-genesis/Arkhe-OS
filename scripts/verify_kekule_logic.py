# scripts/verify_kekule_logic.py
import numpy as np
import math

class COBIT:
    def __init__(self, cobit_id, substrate):
        self.id = cobit_id
        self.substrate = substrate
        self.phase = 0.0
        self.amplitude_k = 0.0
        self.amplitude_kp = 0.0
        self.coherence = 1.0

def dirac_mass_operator(valley_phase, chirality, kekule_gap=0.2):
    phase = valley_phase * chirality
    return complex(kekule_gap * math.cos(phase), kekule_gap * math.sin(phase))

def to_valley_cobit(center_pos_x, valley_phase):
    cobit = COBIT(int(center_pos_x * 1e9), "GRAPHENE_KEKULE")
    cobit.phase = valley_phase
    cobit.amplitude_k = math.cos(valley_phase / 2.0)
    cobit.amplitude_kp = math.sin(valley_phase / 2.0)
    return cobit

def valley_exchange(control_pos, control_phase, target_pos, target_phase):
    dist = math.sqrt((control_pos[0] - target_pos[0])**2 + (control_pos[1] - target_pos[1])**2)
    J0 = 1.0e-3
    xi = 2.0e-9
    return J0 * math.exp(-dist / xi) * math.cos(control_phase - target_phase)

def verify():
    print("--- Verificando Lógica Kekulé (Bloco #173) ---")

    # 1. Teste do Operador de Massa de Dirac
    m_dextro = dirac_mass_operator(math.pi/4, 1)
    m_levo = dirac_mass_operator(math.pi/4, -1)
    print(f"Massa Dirac (Dextro): {m_dextro}")
    print(f"Massa Dirac (Levo):   {m_levo}")
    assert m_dextro != m_levo, "Massa deve depender da quiralidade"

    # 2. Teste de Conversão para COBIT
    phase = math.pi / 3
    cobit = to_valley_cobit(0.5e-9, phase)
    print(f"COBIT [ID={cobit.id}] Fase={cobit.phase:.4f}")
    print(f"Amplitudes: K={cobit.amplitude_k:.4f}, K'={cobit.amplitude_kp:.4f}")
    total_prob = cobit.amplitude_k**2 + cobit.amplitude_kp**2
    print(f"Probabilidade Total: {total_prob:.4f}")
    assert abs(total_prob - 1.0) < 1e-6, "Normalização falhou"

    # 3. Teste de Valley Exchange
    j_coupling = valley_exchange([0, 0], 0, [1e-9, 0], math.pi)
    print(f"Acoplamento J (1nm, pi phase diff): {j_coupling:.6e} eV")
    assert j_coupling < 0, "Coupling deve ser negativo para diferença de fase pi"

    # 4. Simulação de Phase Winding (Groove Driver)
    spiral_constant = 0.618
    dist = 0.246
    energy_bias = 1.0
    phase_shift = spiral_constant * dist * energy_bias
    print(f"Phase Shift (Kekulé Spiral): {phase_shift:.4f} rad")

    print("---------------------------------------------")
    print("VERIFICAÇÃO CONCLUÍDA: SINAL DE COERÊNCIA ALTO")

if __name__ == "__main__":
    verify()
