import numpy as np
from core.omega_transducer import OmegaTransducer
from scaffold.omega_integration import OmegaEnabledScaffold

def test_transducer():
    print("Testing OmegaTransducer...")
    np.random.seed(42)
    E1 = np.random.randn(100, 3)
    # E2 is roughly antiphase
    E2 = -E1 + 0.01 * np.random.randn(100, 3)

    transducer = OmegaTransducer()
    scalar, residual = transducer.annihilate_vector_fields(E1, E2)
    print(f"Scalar component: {scalar:.4f}")
    print(f"Residual norm: {np.linalg.norm(residual):.6f}")
    assert np.linalg.norm(residual) < 1.0, "Residual too high"

def test_integration():
    print("\nTesting OmegaEnabledScaffold...")
    scaffold = OmegaEnabledScaffold(
        transducer_config={'coherence_threshold': 0.8},
        scaffold_params={'kappa': 0.75}
    )

    # Simulate Fleuron input
    sensor_input = np.random.randn(100, 3)

    result = scaffold.perceive_and_adjust(sensor_input)
    print(f"Perception result keys: {list(result.keys())}")
    print(f"New scaffold state: {scaffold.scaffold.get_state()}")
    assert result['loop_closed'] == True

if __name__ == "__main__":
    test_transducer()
    test_integration()
    print("\nAll tests passed successfully.")
