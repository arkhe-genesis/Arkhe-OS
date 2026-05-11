import sys
from core.torsion_phonon import TorsionPhononField

def run_simulation():
    print("Testing Torsion Phonon Emission...")
    # Change tc so resonance occurs at t > 0
    # t_res = omega_delta/omega_vacuum - t_c = 1.0 - t_c = 1.0 - 0.0 = 1.0 (if tc = 0)
    # wait, omega_delta/omega_vacuum = 1.0. So t_res = 1.0 - tc
    # Let's set tc = -4.0 so t_res = 5.0
    # No, wait, if t_c = 5.0, then t_res = -4.0. We can just test from -5 to 5.

    sim = TorsionPhononField(n_layers=12)
    history = sim.simulate_emission_sequence(-5.0, 5.0, dt=0.01)

    num_emissions = len(history["emissions"])
    final_coherence = history["coherence"][-1]

    print(f"✅ Simulated {num_emissions} phonon emissions")
    print(f"✅ Final coherence: {final_coherence:.3f}")

if __name__ == "__main__":
    run_simulation()
