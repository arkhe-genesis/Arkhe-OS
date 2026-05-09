# tests/test_skyrmion_invariant_corrected.py
import argparse
from core.topology.skyrmion_programmer import generate_texture_bp, SkyrmionType
from core.topology.skyrmion_invariant import compute_skyrmion_charge_lattice

def test_bp_skyrmion_charge_convergence(resolutions=[128, 256, 512]):
    """Belavin-Polyakov skyrmion should yield Q≈1.0 with corrected formula."""

    for res in resolutions:
        n_field = generate_texture_bp(target_charge=1, skyrmion_type=SkyrmionType.NEEL, core_radius=10.0, resolution=(res, res))
        Q = compute_skyrmion_charge_lattice(n_field)
        error = abs(Q - 1.0)
        assert error < 0.15, f"Q={Q:.4f} at res={res} exceeds tolerance"
        print(f"✅ Resolution {res}×{res}: Q={Q:.4f}, error={error:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test BP skyrmion charge convergence.")
    parser.add_argument("--resolutions", type=str, default="128,256,512", help="Comma-separated resolutions to test")
    args = parser.parse_args()

    resolutions = [int(r) for r in args.resolutions.split(",")]
    test_bp_skyrmion_charge_convergence(resolutions)
