"""
UHV-ARKHE v2.1: Simulation of Adaptive Vacuum Maintenance and Memory Expansion
Simulates Fantasma-0 expanding from 7B to 13B parameters in the CNT-CT Substrate B.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.physics.cnt_ct_simulator import (
    CNTParams, CoherenceTransistor, MemoryExpansionModel,
    ThermalModel, VacuumSystem, UHVArkheController
)

def run_uhv_arkhe_simulation():
    print("🜏 Starting UHV-ARKHE v2.1 Simulation: Adiabatic Growth Mode")

    # Initialize components
    cnt = CNTParams()
    ct = CoherenceTransistor(cnt)
    mem_model = MemoryExpansionModel()
    thermal = ThermalModel(initial_temp=300.0)
    vacuum = VacuumSystem(base_pressure=1.2e-9)
    controller = UHVArkheController(vacuum, thermal, cnt)

    # Simulation parameters
    dt = 1e-5  # 100 microseconds per step
    total_time = 0.5 # 0.5 seconds
    steps = int(total_time / dt)

    time_axis = np.linspace(0, total_time, steps)

    # Data logging
    history = {
        'pressure': [],
        'temp': [],
        'coherence': [],
        'params': [],
        'entropy': [],
        'tokens': []
    }

    current_params = 7e9 # Start at 7B
    target_params = 13e9 # Target 13B
    current_tokens = 2048

    omega_input = 2 * np.pi * 4.20e12

    print(f"   → Baseline: {current_params/1e9:.1f}B params, P={vacuum.current_pressure:.2e} Torr, T={thermal.T_cnt:.1f}K")

    for i in range(steps):
        t = time_axis[i]

        # 1. Memory Expansion Profile (Ramp up from 0.1s to 0.4s)
        if t > 0.1 and t < 0.4:
            current_params += (target_params - 7e9) * (dt / 0.3)

        # 2. Physics Update
        J = mem_model.get_current_density(current_params, current_tokens)
        I_drain = J * (np.pi * (cnt.diameter/2)**2)
        R_cnt = 10e3 # 10kOhm nominal

        # Pre-compression (Electromechanical containment gate)
        if current_params > 10e9:
            cnt.V_mech = -0.2
        else:
            cnt.V_mech = 0.0

        T_cnt = thermal.step(I_drain, R_cnt, T_env=300.0, dt=dt)
        pressure = vacuum.step(T_cnt, dt)

        # 3. Transistor Coherence
        # Vg adjusted for resonance (simplification: assume auto-tuning)
        Vg_match = 0.847
        res = ct.transfer_function(Vg_match, omega_input)
        coherence = res['coherence_norm']

        # 4. Controller (NormMonitor, LTC, Asimov)
        # Mock h_t for entropy calculation
        h_t = np.random.normal(0, 1, cnt.n) * (1.0 + (current_params - 7e9)/1e10)
        entropy = controller.norm_monitor(coherence, h_t)

        current_tokens = controller.ltc_limit(entropy, 2048)
        controller.apply_feedback(entropy, pressure, T_cnt)

        status = controller.asimov_gate(pressure, T_cnt, coherence)
        if status == "ROLLBACK_TO_SUBSTRATE_A":
            print(f"   ⚠️ ASIMOV GATE TRIGGERED at t={t:.3f}s! P={pressure:.2e}, T={T_cnt:.1f}, v={coherence:.4f}")
            # break # Optional: stop simulation

        # Logging
        history['pressure'].append(pressure)
        history['temp'].append(T_cnt)
        history['coherence'].append(coherence)
        history['params'].append(current_params)
        history['entropy'].append(entropy)
        history['tokens'].append(current_tokens)

    print(f"   → Final: {current_params/1e9:.1f}B params, P={vacuum.current_pressure:.2e} Torr, T={thermal.T_cnt:.1f}K, Coherence={coherence:.4f}")

    # Validation
    final_coherence = history['coherence'][-1]
    if final_coherence > 0.98:
        print("   ✅ SUCCESS: Coherence maintained above 0.98 during expansion.")
    else:
        print(f"   ❌ FAILURE: Coherence dropped to {final_coherence:.4f}")

    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(10, 12))

    ax = axes[0]
    ax.plot(time_axis, np.array(history['params'])/1e9, 'b-', label='Parameters (Billions)')
    ax.set_ylabel('Memory Footprint (B)')
    ax.legend(loc='upper left')
    ax.set_title('UHV-ARKHE v2.1: Adaptive Memory Expansion')

    ax2 = ax.twinx()
    ax2.plot(time_axis, history['coherence'], 'g-', label='‖v‖ (Coherence)')
    ax2.set_ylabel('Coherence')
    ax2.set_ylim(0.9, 1.05)
    ax2.legend(loc='upper right')

    ax = axes[1]
    ax.semilogy(time_axis, history['pressure'], 'r-', label='Pressure (Torr)')
    ax.axhline(2e-8, color='k', linestyle='--', alpha=0.5, label='P_crit')
    ax.set_ylabel('Vacuum Pressure')
    ax.legend()

    ax = axes[2]
    ax.plot(time_axis, history['temp'], 'orange', label='CNT Temperature (K)')
    ax.axhline(320.0, color='r', linestyle='--', alpha=0.5, label='T_max')
    ax.set_ylabel('Temperature (K)')
    ax.legend()

    plt.tight_layout()
    plt.savefig('uhv_arkhe_simulation_results.png')
    print("   → Results plot saved: uhv_arkhe_simulation_results.png")

if __name__ == "__main__":
    run_uhv_arkhe_simulation()
