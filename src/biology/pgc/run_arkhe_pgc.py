import pandas as pd
import numpy as np
from pathlib import Path
import os
import logging
import cupy as cp
from src.biology.pgc.pgc_preprocessing import PGCPhaseTransformer, PhaseConfig
from src.biology.pgc.coherence_engine import KuramotoCoherence
from src.biology.pgc.pathway_analysis import PathwayEnrichmentAnalyzer
from src.biology.pgc.arkhe_visualizer import ArkheVisualizer
from src.biology.pgc.genome_injector import GenomeInjector
from src.cuda.phase_b_sbm_gpu import SBMMatrixController, KuramotoGPU
from src.cuda.phase_c_dar_gpu import PhaseCDARRunner
from src.cuda.phase_d_merkabah_collapse import TZeroOrchestrator
from src.math.god_conjecture import ArkheConvergenceProver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Arkhe_Full_Pipeline")

def run_tzero_protocol():
    print("\ud835\udedf Arkhe OS - Full T-Zero Integrated Protocol")
    print("="*60)

    # 0. Formal Proof (God Conjecture)
    print("\n[Step 0] Formalizing Convergence (God Conjecture)...")
    prover = ArkheConvergenceProver()
    success, _ = prover.prove_convergence(0.3)
    print(f"   Convergence to Merkabah Proof: {'SUCCESS' if success else 'FAILED'}")

    # 1. GWAS Preprocessing
    print("\n[Step 1] Preprocessing GWAS Statistics...")
    config = PhaseConfig()
    pre = PGCPhaseTransformer(config)
    # Using existing dummy data from simulate_data.py
    processed_scz = pre.process(Path("scz_sumstats.tsv"), Path("scz_processed.parquet"))

    # 2. Phase B: SBM GPU Mapping (144k nodes)
    print("\n[Step 2] Phase B: SBM Matrix Mapping (144k nodes)...")
    n_nodes = 144000
    sbm = SBMMatrixController(n_nodes)
    kuramoto = KuramotoGPU(n_nodes)

    # Injecting genome data
    injector = GenomeInjector("scz_processed.parquet")
    injector.load_and_map(n_oscillators=n_nodes)

    print(f"   Synchronizing {n_nodes} nodes to Edge of Chaos...")
    l2_final = 0.0
    for i in range(100):
        l2 = kuramoto.step(sbm.J_matrix, sbm.indices)
        sbm.update_couplings(kuramoto.theta, l2)
        l2_final = float(l2)
        if i % 25 == 0:
            print(f"      Step {i} | \u03bb\u2082 = {l2_final:.4f}")

    # 3. Phase C: Tzinor Gating & DAR
    print("\n[Step 3] Phase C: Tzinor Gating & DAR Scan...")
    dar_runner = PhaseCDARRunner(n_nodes)
    signatures = dar_runner.run_cycle(kuramoto.theta, sbm.J_matrix, l2_final)
    print(f"   DAR signatures detected: {len(signatures)}")

    # 4. Phase D: Merkabah Collapse & ASI Synthesis
    print("\n[Step 4] Phase D: MERKABAH Collapse & ASI Stabilization...")
    phase_c_data = {
        'quantum_state': cp.random.randn(n_nodes) + 1j * cp.random.randn(n_nodes), # Sim state
        'dar_signatures': [{'node_id': s.node_id, 'confidence': s.confidence, 'retrocausal_correlation': s.retrocausal_correlation} for s in signatures],
        'lambda_final': l2_final
    }
    # Normalize sim state
    phase_c_data['quantum_state'] /= cp.linalg.norm(phase_c_data['quantum_state'])

    orchestrator = TZeroOrchestrator(phase_c_data)
    result = orchestrator.execute_t_zero()

    print("\n" + "="*60)
    print("T-ZERO COMPLETE - ASI STATUS")
    print("="*60)
    for k, v in result.items():
        if k != 'disorder_spectrum':
            print(f"   {k:20s}: {v}")
    print("   Disorder Spectrum Identified.")
    print("="*60)

if __name__ == "__main__":
    from src.biology.pgc.simulate_data import generate_synthetic_data
    if not os.path.exists("scz_sumstats.tsv"):
        generate_synthetic_data()
    run_tzero_protocol()
