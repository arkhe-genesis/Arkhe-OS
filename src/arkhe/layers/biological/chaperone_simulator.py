import random
import numpy as np

class ChaperoneOracle:
    """
    Simulates a chaperone projection oracle.
    State tends towards coherence (native fold) with coupling phi_c.
    """
    def __init__(self, name: str, phi_c: float, description: str):
        self.name = name
        self.phi_c = phi_c
        self.description = description

    def apply_projection(self, current_state: float, target_state: float, noise: float) -> float:
        """
        Projects the current state closer to the target (native) state,
        dampening noise based on the coupling constant phi_c.
        """
        # Linear interpolation with noise reduction
        return current_state * (1 - self.phi_c) + self.phi_c * (target_state - noise * (1 - self.phi_c))

class FoldingSimulation:
    def __init__(self, target_state: float = 1.0, max_steps: int = 50):
        self.target_state = target_state
        self.max_steps = max_steps

    def simulate(self, chaperone: ChaperoneOracle = None, noise_level: float = 0.2) -> dict:
        state = 0.0 # Starts unfolded
        history = [state]

        for step in range(self.max_steps):
            noise = random.uniform(-noise_level, noise_level)

            # Natural thermal folding attempts (very slow/random without chaperone)
            natural_drift = random.uniform(0, 0.05)
            state += natural_drift + noise

            # Apply chaperone oracle if present
            if chaperone:
                state = chaperone.apply_projection(state, self.target_state, noise)

            # Cap state at 1.0 (fully folded) and 0.0 (fully unfolded)
            state = max(0.0, min(1.0, state))
            history.append(state)

            if state >= 0.99:
                break

        return {
            "chaperone": chaperone.name if chaperone else "None",
            "steps_to_fold": len(history) - 1 if state >= 0.99 else self.max_steps,
            "final_state": state,
            "history": history
        }

def run_chaperone_comparison():
    hsp70 = ChaperoneOracle("Hsp70", phi_c=0.6, description="RNA/Protein coherence stabilizer")
    groel = ChaperoneOracle("GroEL", phi_c=0.85, description="High-efficiency folding chamber")

    sim = FoldingSimulation(max_steps=100)

    print("--- Chaperone Folding Simulation ---")

    # 1. No Chaperone
    res_none = sim.simulate(chaperone=None, noise_level=0.15)
    print(f"No Chaperone : Final State = {res_none['final_state']:.2f}, Steps = {res_none['steps_to_fold']}")

    # 2. Hsp70
    res_hsp70 = sim.simulate(chaperone=hsp70, noise_level=0.15)
    print(f"Hsp70 (phi=0.6) : Final State = {res_hsp70['final_state']:.2f}, Steps = {res_hsp70['steps_to_fold']}")

    # 3. GroEL
    res_groel = sim.simulate(chaperone=groel, noise_level=0.15)
    print(f"GroEL (phi=0.85): Final State = {res_groel['final_state']:.2f}, Steps = {res_groel['steps_to_fold']}")

    return res_none, res_hsp70, res_groel

if __name__ == "__main__":
    run_chaperone_comparison()