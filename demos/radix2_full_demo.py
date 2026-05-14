#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radix2_full_demo.py — Demonstração completa: RADIX‑2 + QNC + Transfer Learning + Hardware
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import time
import json
import hashlib
from arkp_qnc.qnc_transfer import MultiSpeciesQNC
from arkp_bio.src.radix2_designer import Radix2Designer, Radix2Spec
from arkp_bio.adaptive_genomic_ecc import AdaptiveGenomicECC
from arkp_bio.quantum_folding_simulator import PhiCField
from arkp_quantum.src.qiskit_backend import QiskitBackend

def run_full_demo():
    print("🧬⚛️ ARKHE Ω‑TEMP v6.4.0 — RADIX‑2 Full Demo")
    print("=" * 70)

    # 1. Inicializar componentes
    print("\n[1/6] Inicializando componentes...")
    qnc = MultiSpeciesQNC(max_len=128, hidden_dim=16)
    ecc = AdaptiveGenomicECC()
    phi_c = PhiCField(coupling_constant=0.1)

    # Registrar espécies para transfer learning
    source_species = [
        "Deinococcus radiodurans",
        "Thermococcus gammatolerans",
        "Rubrobacter radiotolerans",
        "Kineococcus radiotolerans",
    ]
    for species in source_species:
        qnc.register_species(species, base_resistance=15.0)

    # 2. Pré-treinar QNC multi-espécie
    print("\n[2/6] Pré-treinamento multi-espécie...")
    # Placeholder: em produção, carregar dataset real de 50+ extremófilos
    pretrain_data = {
        species: [(f"{species[:20]}{'ATGC'*10}", 1) for _ in range(10)]
        for species in source_species
    }
    pretrain_loss = qnc.pretrain_on_all_species(pretrain_data, epochs=20)
    print(f"   Loss final pré-treino: {pretrain_loss[-1]:.6f}")

    # 3. Projetar RADIX‑2 via transfer learning
    print("\n[3/6] Projetando RADIX‑2 via transfer learning...")
    designer = Radix2Designer(qnc, ecc, phi_c)
    radix2_result = designer.optimize_via_transfer_learning(
        source_species=source_species,
        target_resistance=50.0,
        max_iterations=50,
    )
    print(f"   Resistência prevista: {radix2_result['predicted_resistance']:.2f} kGy")
    print(f"   Coerência Φ_C prevista: {radix2_result['predicted_phi_c']:.4f}")
    print(f"   Prova de integridade: {radix2_result['integrity_proof']}")

    # 4. Testar reparo adaptativo
    print("\n[4/6] Testando reparo adaptativo...")
    from arkp_bio.src.adaptive_repair_engine import AdaptiveRepairEngine
    repair_engine = AdaptiveRepairEngine(qnc, ecc, phi_c)

    # Simular dano em RADIX‑2
    damaged_seq = radix2_result["optimized_sequence"][:1000] + "XXXX" + radix2_result["optimized_sequence"][1004:]
    decision = repair_engine.assess_damage_and_repair(
        damaged_sequence=damaged_seq,
        radiation_level=30.0,
        species_context="RADIX-2",
    )
    print(f"   Decisão de reparo: {decision.action} (confiança: {decision.confidence:.2%})")
    print(f"   Impacto previsto em Φ_C: {decision.phi_c_impact:+.4f}")

    # 5. Executar em hardware quântico (simulado)
    print("\n[5/6] Executando circuito QNC em backend quântico...")
    quantum_backend = QiskitBackend(backend_name="ibmq_qasm_simulator", use_real_hardware=False)

    # Codificar estado quântico do embedding RADIX‑2
    adapted = qnc.encode_species(radix2_result["optimized_sequence"][:64], "RADIX-2")
    circuit = quantum_backend.encode_quantum_state(adapted, num_qubits=4)

    # Executar circuito
    result = quantum_backend.execute_qnc_circuit(circuit, shots=1024)
    proof = quantum_backend.compute_integrity_proof(circuit, result)

    print(f"   Resultados: {len(result['counts'])} estados únicos")
    print(f"   Prova de integridade quântica: {proof}")

    # 6. Relatório consolidado
    print("\n[6/6] Relatório consolidado:")
    print(f"   ✅ RADIX‑2 projetado com resistência >50 kGy: {radix2_result['predicted_resistance'] >= 50.0}")
    print(f"   ✅ Coerência Φ_C >0.999: {radix2_result['predicted_phi_c'] >= 0.999}")
    print(f"   ✅ Transfer learning eficiente: {pretrain_loss[-1] < 0.1}")
    print(f"   ✅ Reparo adaptativo funcional: {decision.action != 'bypass'}")
    print(f"   ✅ Execução quântica validada: {len(result['counts']) > 0}")

    print(f"\n🔐 Selo canônico final: {hashlib.sha3_256(json.dumps({
        'radix2_proof': radix2_result['integrity_proof'],
        'quantum_proof': proof,
        'timestamp': time.time(),
    }, default=str).encode()).hexdigest()[:16]}")

    print(f"\n✨ Demo concluída — RADIX‑2 pronto para validação experimental!")

if __name__ == "__main__":
    run_full_demo()
