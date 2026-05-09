# examples/plasmonic_closed_loop_skyrmion.py
"""
ARKHE Plasmonic Testbed: Full A∘P Loop Execution
Programs a Néel-type skyrmion with Q=+1, runs closed-loop correction until convergence.
"""
import numpy as np
from core.topology.skyrmion_programmer import SkyrmionProgrammer
from core.topology.plasmonic_hardware_bridge import PlasmonicHardwareBridge, SLMConfig
from core.topology.snom_reader import SNOMReader
from core.topology.adaptive_topology_loop import AdaptiveTopologyController

# 1. Initialize components
programmer = SkyrmionProgrammer()
hardware = PlasmonicHardwareBridge(SLMConfig(), simulation_mode=True)
reader = SNOMReader(noise_level=0.05)  # 5% measurement noise
controller = AdaptiveTopologyController(
    programmer=programmer,
    hardware=hardware,
    reader=reader,
    convergence_threshold=0.05,
    max_iterations=8,
    learning_rate=0.15
)

# 2. Run closed-loop optimization
print("🔬 ARKHE Plasmonic Testbed — Closing the A∘P Loop")
print("=" * 60)
print(f"Target: Néel skyrmion, Q=+1, initial core_radius=12nm, E_z=1e6 V/m")
print()

result = controller.close_loop(
    Q_target=1,
    texture_type="néel",
    initial_core_radius=12.0,
    external_field=1e6
)

# 3. Report results
print(f"\n📊 Loop Summary:")
print(f"  Converged: {result['converged']}")
print(f"  Iterations: {result['iterations']}")
print(f"  Final Q_measured: {result['final_Q_measured']:.3f}")
print(f"  Final error: {result['final_error']:.4f}")
print(f"  Final core_radius: {result['final_program'].core_radius:.1f} nm")
print(f"  Final E_z: {result['final_program'].control_fields['E_z']:.1e} V/m")
print(f"  Total excitation time: {sum(result['loop_stats'].excitation_time_ms):.1f} ms")
print(f"  Total readout time: {sum(result['loop_stats'].readout_time_ms):.1f} ms")
