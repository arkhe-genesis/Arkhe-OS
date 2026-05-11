import os
import sys
import numpy as np

# Adicionar src ao path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from arkhe_core.architecture.casulo_pipeline import unified_arkhe_pipeline
    import jax
    import scipy
    print("Dependencies loaded correctly.")
except ImportError as e:
    print(f"Error loading dependencies: {e}")
    sys.exit(1)

def verify_pipeline():
    print("=== VERIFYING ARKHE v1.0 UNIFIED PIPELINE ===")

    # Simulando backend_props para 127 qubits Heavy-Hex
    np.random.seed(42)
    n = 127
    # Gerar mapa de acoplamento Heavy-Hex simplificado
    coupling = [(i, i+1) for i in range(n-1)] + [(i, i+2) for i in range(0, n-2, 3)]
    backend_props = {
        'coupling_map': coupling,
        't1': np.random.normal(150.0, 80.0, n).clip(10, 500),
        't2': np.random.normal(110.0, 60.0, n).clip(5, 400),
        'readout_error': np.random.uniform(0.005, 0.03, n)
    }

    try:
        result = unified_arkhe_pipeline(backend_props)

        print(f"λ₂ (Algebraic Connectivity): {result['lambda2']:.6f}")
        print(f"Qubits Cut: {len(result['phases']['cut'])}")
        print(f"Qubits Mid: {len(result['phases']['mid'])}")
        print(f"Qubits Bulk: {len(result['phases']['bulk'])}")

        # Check for NaNs
        alpha_cut = result['soc']['alpha_cut']
        alpha_bulk = result['soc']['alpha_bulk']
        print(f"α_cut: {alpha_cut:.3f}, α_bulk: {alpha_bulk:.3f}")

        if np.isnan(alpha_cut) or np.isnan(alpha_bulk):
            print("FAILED: NaN detected in SOC analysis.")
            sys.exit(1)

        # Check Casulo Modes
        eigvals = result['casulo_modes']['eigenvalues']
        print(f"First 5 Casulo Eigenvalues: {eigvals[:5]}")

        if len(eigvals) == 0:
            print("FAILED: No eigenvalues found in Casulo modes.")
            sys.exit(1)

        print("\nPIPELINE VERIFICATION SUCCESSFUL!")

    except Exception as e:
        print(f"PIPELINE VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_pipeline()
