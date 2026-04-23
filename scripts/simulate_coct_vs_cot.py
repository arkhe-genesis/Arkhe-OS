"""
Simulation Script: CoT vs CoCT Performance Analysis
Measures reasoning coherence (λ₂) and generates report for Arkhe(n) Consórcio.
"""

import numpy as np
import json
import os
import sys

# Ensure arkhe-brain is in path
sys.path.append(os.path.join(os.getcwd(), "arkhe-brain"))
from latent_coherence import CoCTSimulator, ReasoningMetrics
from datetime import datetime, timezone

def run_performance_comparison(num_steps=12, hidden_dim=512):
    print("="*70)
    print("EXPERIMENTO: CoT Tokenizado vs. CoCT Latente")
    print(f"Dimensão Latente: {hidden_dim} | Passos: {num_steps}")
    print("="*70)

    sim = CoCTSimulator(hidden_dim=hidden_dim, batch_size=32)

    # 1. Simulate Chain of Thought (Tokenized)
    cot_history = sim.simulate_cot(num_steps)

    # 2. Simulate Chain of Continuous Thought (Latent)
    coct_history = sim.simulate_coct(num_steps)

    # 3. Consolidate results
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_steps": num_steps,
            "hidden_dim": hidden_dim,
            "varela_threshold": 0.847,
            "ep_threshold": 0.999
        },
        "cot": [
            {
                "step": m.step,
                "lambda2": m.lambda2,
                "entropy": m.entropy_svd,
                "status": m.coherence_status
            } for m in cot_history
        ],
        "coct": [
            {
                "step": m.step,
                "lambda2": m.lambda2,
                "entropy": m.entropy_svd,
                "status": m.coherence_status
            } for m in coct_history
        ],
        "summary": {
            "avg_lambda_cot": float(np.mean([m.lambda2 for m in cot_history])),
            "avg_lambda_coct": float(np.mean([m.lambda2 for m in coct_history])),
            "peak_lambda_coct": float(np.max([m.lambda2 for m in coct_history])),
            "ep_reached": any(m.lambda2 >= 0.999 for m in coct_history)
        }
    }

    # 4. Save to JSON for backend/frontend ingestion
    output_path = "latent_reasoning_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Resultados salvos em: {output_path}")
    print(f"   CoT λ₂ médio: {results['summary']['avg_lambda_cot']:.4f}")
    print(f"   CoCT λ₂ médio: {results['summary']['avg_lambda_coct']:.4f}")
    print(f"   CoCT EP Atingido: {'SIM' if results['summary']['ep_reached'] else 'NÃO'}")

    return results

if __name__ == "__main__":
    run_performance_comparison()
