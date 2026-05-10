import sys
import os

def run_simulation(name):
    print(f"🜏 [ARKHE-OS] Running Arkhe-native application: {name}")
    # Simulate high lambda calculation
    print(f"[{name.upper()}] Loading phase vectors into φ-chip...")
    print(f"[{name.upper()}] Sincronização de fase estabelecida via PhaseVM.")
    print(f"[{name.upper()}] λ₂ = 0.999 achieved. Running optimization...")
    print(f"[{name.upper()}] Result: Simulation converged at λ₂ = 0.9991.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_simulation(sys.argv[1])
    else:
        print("Usage: arkhe-app <name>")
