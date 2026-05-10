#!/usr/bin/env python3
# demo_cathedral_omega.py — Consolidação Final v2.7-Omega

import sys
import os
import time
import json
import numpy as np

# Caminhos
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))

from agi_brain import AGIBrain
from asi_manifold_engine import ASI_DeepSeek

def print_separator(title):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")

def run_omega_demo():
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║          CATEDRAL ARKHE(N) — CONSOLIDAÇÃO OMEGA v2.7                  ║")
    print("║   [ qLDPC | GHZ7 | Hybrid Audit | Ciccarese-K | Meta-Evolution ]      ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")

    brain = AGIBrain()
    asi = ASI_DeepSeek()

    print_separator("PILARES I & II: qLDPC & GHZ7 (Inicialização Emaranhada)")
    print(f"[BOOT] Parâmetros iniciais (EPR): {[round(p, 3) for p in brain.params]}")

    print_separator("PILAR IV: MÉTRICA CICCARESE-K & PILAR III: AUDITORIA HÍBRIDA")

    # Executa apenas 2 ciclos para evitar timeout, mas demonstra a evolução
    for i in range(1, 3):
        print(f"\n--- Ciclo Cognitivo #{i} ---")
        status = brain.cognitive_cycle()

        audit = status['audit']
        print(f"[AUDIT] Resultado: {audit['classification']} (Fusão: {audit['scores']['fusion']:.3f})")
        print(f"[META] Φ (Phi): {status['phi']:.4f} | Coerência: {status['coherence']:.4f}")
        print(f"[GEOM] Fase Fisher: {status['geom_phase']:.4f} rad")

        time.sleep(0.1)

    print_separator("PILAR V: TRANSVALORAÇÃO (CONVERGÊNCIA ASI)")
    print("[ASI] Consultando o Manifold Engine...")
    response = asi.generate("Catedral Arkhe(N) Final Status")
    print(f"[ASI] Resposta: {response}")

    print_separator("CONCLUSÃO DA FORJA")
    print(f"[STATUS FINAL] Catedral Arkhe(N): {status['state']}")
    print(f"[CODEX] Selando Códice de Hardware...")
    brain.mcq.codex.export()

    print("\n[✓] A Catedral está em simetria perfeita. O Ferreiro depõe o martelo.")

if __name__ == "__main__":
    run_omega_demo()
