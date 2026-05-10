# examples/causal_order_demo.py
"""
ARKHE OS v∞.430.1 — Substrate 91: Variable Causal Order Simulator
Interactive Demo
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.temporal.causal_order_simulator import CausalOrderSimulator, CausalOrderConfig
from ui.causal_order_controller import CausalOrderController

def main():
    print("Initializing Substrate 91 Causal Order Simulator...")

    config = CausalOrderConfig(
        grid_size=128,
        causal_order=0.0,  # Start in atemporal regime
        noise_amplitude=0.08,
        time_step=0.01,
    )

    # We use None for canvas to run purely through matplotlib for this demo
    simulator = CausalOrderSimulator(config, canvas=None)

    controller = CausalOrderController(simulator)
    controller.show()

if __name__ == "__main__":
    main()
