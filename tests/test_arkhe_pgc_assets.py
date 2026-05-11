import pytest
import os
from src.biology.pgc.run_arkhe_pgc import run_full_analysis
from src.biology.pgc.simulate_data import generate_synthetic_data

def test_arkhe_pgc_asset_generation(tmp_path):
    """
    Verifies that the Arkhe-PGC pipeline generates the required visual assets.
    """
    # Change to temp directory to avoid cluttering root
    os.chdir(tmp_path)

    # 1. Generate Data
    generate_synthetic_data()

    # 2. Run Analysis
    run_full_analysis()

    # 3. Assertions
    assert os.path.exists("venn_overlap.png")
    assert os.path.exists("phase_radar.png")
    assert os.path.exists("scz_processed.parquet")
    assert os.path.exists("bip_processed.parquet")

    print("Asset generation test passed.")

if __name__ == "__main__":
    # For manual trigger
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_arkhe_pgc_asset_generation(tmp)
