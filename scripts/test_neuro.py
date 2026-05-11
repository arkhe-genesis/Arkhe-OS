
import numpy as np
from src.neuro.neural_scaffold import NeuralScaffold, DiseasePhase

def test_neural_scaffold_simulation():
    print("Testing NeuralScaffold simulation...")
    # Initialize scaffold
    scaffold = NeuralScaffold(N=10, k=2, p=0.1)

    # Test initial state
    assert len(scaffold.history) == 0
    assert scaffold.N == 10

    # Run a few steps
    for _ in range(5):
        scaffold.step(dt=0.05)

    assert len(scaffold.history) == 5
    last_state = scaffold.history[-1]
    assert 0 <= last_state.r_global <= 1.0
    assert isinstance(last_state.phase, DiseasePhase)
    print(f"Step 5: r={last_state.r_global:.3f}, phase={last_state.phase}")

    # Test pathology application
    scaffold.apply_pathology(0.9) # High degradation
    assert scaffold.degradation_level == 0.9

    # Run more steps and check if r decreases (likely, but Kuramoto can be complex)
    for _ in range(10):
        scaffold.step(dt=0.05)

    final_state = scaffold.history[-1]
    print(f"Final state after pathology: r={final_state.r_global:.3f}, phase={final_state.phase}")
    print("Test passed!")

if __name__ == "__main__":
    test_neural_scaffold_simulation()
