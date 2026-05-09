# tests/test_adaptive_controller.py
import argparse
from core.topology.skyrmion_programmer import SkyrmionProgrammer
from core.topology.plasmonic_hardware_bridge import PlasmonicHardwareBridge, SLMConfig
from core.topology.snom_reader import SNOMReader
from core.topology.adaptive_topology_loop import AdaptiveTopologyController

def test_controller(q_target, initial_radius, noise):
    print(f"Testing adaptive controller with Q_target={q_target}, initial_radius={initial_radius}, noise={noise}")
    programmer = SkyrmionProgrammer()
    hardware = PlasmonicHardwareBridge(SLMConfig(), simulation_mode=True)
    reader = SNOMReader(noise_level=noise)

    controller = AdaptiveTopologyController(
        programmer=programmer,
        hardware=hardware,
        reader=reader,
        convergence_threshold=0.05,
        max_iterations=10,
        learning_rate=0.15
    )

    result = controller.close_loop(
        Q_target=q_target,
        texture_type="néel",
        initial_core_radius=initial_radius,
        external_field=1e6
    )

    print(f"\n📊 Test Summary:")
    print(f"  Converged: {result['converged']}")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Final Q_measured: {result['final_Q_measured']:.3f}")

    if result['converged']:
        print("✅ Controller successfully converged.")
    else:
        print("❌ Controller failed to converge within max iterations.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test adaptive topology controller.")
    parser.add_argument("--Q-target", type=int, default=2, help="Target topological charge.")
    parser.add_argument("--initial-radius", type=float, default=8.0, help="Initial core radius in nm.")
    parser.add_argument("--noise", type=float, default=0.10, help="Measurement noise level.")
    args = parser.parse_args()

    test_controller(args.Q_target, args.initial_radius, args.noise)
