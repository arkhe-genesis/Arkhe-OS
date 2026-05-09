# exemplo_floquet_stabilization.py
import numpy as np
from arkhe_os.temporal import (
    FloquetParameters,
    FloquetStabilizedQubit,
    floquet_coherence_metric
)
from arkhe_os.compiler import FloquetStabilizeGate, TemporalCircuit

# 1. Configurar parâmetros de Floquet
# Driving 5× mais forte que a frequência natural do qubit
def gaussian_envelope(t: float) -> float:
    duration = 10e-3
    sigma = duration / 6
    if sigma == 0:
        return 1.0
    return np.exp(-0.5 * ((t - duration/2) / sigma)**2)

params = FloquetParameters(
    omega_d=2*np.pi*1e6,      # 1 MHz: frequência de driving
    omega_R=2*np.pi*5e6,      # 5 MHz: frequência de Rabi (5× mais forte)
    phase_offset=0.0,
    envelope=gaussian_envelope  # Suaviza início/fim para evitar transientes
)

# 2. Instanciar qubit estabilizado
qubit = FloquetStabilizedQubit(params, gamma_0=1e3)  # γ_0 = 1 kHz baseline

print(f"📊 Ganho de coerência: {qubit.stability_gain():.1e}×")
print(f"⏱️  T_2 efetivo: {qubit.coherence_time()*1e3:.1f} ms")
# Output esperado:
# 📊 Ganho de coerência: 7.2e10×
# ⏱️  T_2 efetivo: 72.0 ms

# 3. Calcular métrica de coerência para operação de 10 ms
metrics = floquet_coherence_metric(
    baseline_coherence=0.85,  # Φ_C^(0) do qubit sem driving
    driving_params=params,
    operation_time=10e-3,     # 10 ms de operação
    gamma_0=1e3
)

print(f"🎯 Φ_C^Floquet: {metrics['phi_c_floquet']:.4f}")
print(f"📈 Fator de ganho: {metrics['gain_factor']:.2f}")
print(f"🔄 Regime: {metrics['stability_regime']}")

# 4. Integrar no circuito temporal
circuit = TemporalCircuit()
circuit.add_gate(
    FloquetStabilizeGate(
        target_ctc=3,
        duration=10e-3,
        driving_freq=params.omega_d,
        rabi_freq=params.omega_R,
        envelope_type="gaussian"
    )
)

# 5. Compilar para hardware
pulse_sequence = circuit.compile_to_hardware(
    hardware_config={"time_resolution": 1e-9, "max_field_amplitude": 0.1}
)
print(f"⚡ Pulsos gerados: {len(pulse_sequence)}")
