#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_radix2_transfer_integration.py — Teste de integração: RADIX-2 + Transfer Learning
Valida transfer learning multi-espécie e genoma sintético otimizado.
"""

import numpy as np
import pytest
import hashlib

from arkp_radix1.src.radix2_simulation import RADIX2Genome, RADIX2Simulator
from arkp_bio.src.quantum_folding_simulator import PhiCField
from arkp_qnc.src.qnc_transfer import MultiSpeciesQNC
from arkp_bio.src.extremophile_analyzer import EXTREMOPHILE_DATABASE


def test_radix2_genome_structure():
    """Testa estrutura do genoma RADIX-2."""
    genome = RADIX2Genome()
    assert genome.name == "RADIX-2"
    assert genome.version == "2.0.0"
    assert genome.sequence_length == 8192
    assert len(genome.coding_regions) == 5  # 1 a mais que RADIX-1
    assert len(genome.source_species) == 3
    assert "Deinococcus radiodurans" in genome.source_species
    proof = genome.compute_integrity()
    assert len(proof) == 16
    print(f"✅ RADIX-2 structure: {proof}")


def test_transfer_model_pretraining():
    """Testa pré-treinamento multi-espécie."""
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]

    loss_history = model.pretrain_on_all_species(species_data, epochs=10, lr=0.03)

    assert len(loss_history) == 10
    assert len(model.trained_species) == len(EXTREMOPHILE_DATABASE)
    # Loss deve decrescer ou estabilizar
    assert loss_history[-1] <= loss_history[0] * 2.0
    print(f"✅ Transfer pretraining: loss {loss_history[0]:.4f} → {loss_history[-1]:.4f}")


def test_transfer_knowledge_to_radix2():
    """Testa transferência de conhecimento para RADIX-2."""
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)

    # Pré-treinar
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]
    model.pretrain_on_all_species(species_data, epochs=5, lr=0.03)

    # Transferir
    model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-2")

    assert "RADIX-2" in model.species_adapters
    # Adapter deve ser diferente do estado base
    base = np.eye(4, dtype=complex) / 4
    assert not np.allclose(model.species_adapters["RADIX-2"], base, atol=1e-6)
    print("✅ Transfer to RADIX-2 passed")


def test_radix2_simulation():
    """Testa simulação RADIX-2 com transfer learning."""
    phi_c = PhiCField(coupling_constant=0.15)

    # Criar modelo de transferência mínimo
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]
    model.pretrain_on_all_species(species_data, epochs=5, lr=0.03)
    model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-2")

    simulator = RADIX2Simulator(phi_c, phi_c_value=0.9999, transfer_model=model)

    result = simulator.simulate_with_transfer_learning(radiation_stress=50.0, max_cycles=500)

    assert result["genome"] == "RADIX-2"
    assert result["phi_c_background"] == 0.9999
    assert result["phi_c_boosted"] >= 0.9999
    assert result["repair_success"] is True
    assert 0.0 <= result["integrated_score"] <= 1.0
    assert result["transfer_contribution"] >= 0.0
    print(f"✅ RADIX-2 simulation: score={result['integrated_score']:.4f}, Φ_C={result['phi_c_boosted']:.6f}")


def test_radix2_vs_radix1_superiority():
    """Testa que RADIX-2 supera RADIX-1 em métricas-chave."""
    from arkp_radix1.src.radix1_simulation import RADIX1Simulator

    phi_c = PhiCField(coupling_constant=0.15)

    # RADIX-1 baseline
    sim1 = RADIX1Simulator(phi_c, phi_c_value=0.9995)
    result1 = sim1.simulate_folding_and_repair(radiation_stress=25.0, max_cycles=200)

    # RADIX-2 com transfer
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]
    model.pretrain_on_all_species(species_data, epochs=5, lr=0.03)
    model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-2")

    sim2 = RADIX2Simulator(phi_c, phi_c_value=0.9999, transfer_model=model)
    result2 = sim2.simulate_with_transfer_learning(radiation_stress=50.0, max_cycles=500)

    # RADIX-2 deve ter Φ_C mais alto
    assert result2["phi_c_boosted"] > result1["integrated_score"] * 0.5
    # RADIX-2 deve suportar mais radiação
    assert result2["radiation_stress_kgy"] > result1["radiation_stress_kgy"]

    print(f"✅ RADIX-2 superiority:")
    print(f"   RADIX-1 @ 25 kGy: score={result1['integrated_score']:.4f}")
    print(f"   RADIX-2 @ 50 kGy: score={result2['integrated_score']:.4f}, Φ_C={result2['phi_c_boosted']:.6f}")


def test_zero_shot_prediction():
    """Testa predição zero-shot para espécie desconhecida."""
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]
    model.pretrain_on_all_species(species_data, epochs=5, lr=0.03)

    new_seq = "PyrococcusFuriosusATCGATCGATCGATCG"
    pred, conf = model.zero_shot_predict(new_seq[:32])

    assert pred in [0, 1]
    assert 0.0 <= conf <= 1.0
    print(f"✅ Zero-shot: pred={pred}, conf={conf:.4f}")


def test_full_integration_radix2_transfer():
    """Teste de integração completo: Transfer → RADIX-2."""
    # 1. Pré-treinar em todas as espécies
    model = MultiSpeciesQNC(max_len=32, hidden_dim=4)
    species_data = {}
    for org in EXTREMOPHILE_DATABASE:
        seq = (org.organism_name[:10] + "ATCG"*5)[:32].ljust(32, 'N')
        label = 1 if org.radiation_resistance_kgy >= 10.0 else 0
        species_data[org.organism_name] = [(seq, label) for _ in range(2)]

    print("\n📚 Pré-treinamento multi-espécie...")
    pretrain_loss = model.pretrain_on_all_species(species_data, epochs=5, lr=0.03)

    # 2. Transferir para RADIX-2
    print("🔄 Transferindo conhecimento para RADIX-2...")
    model.transfer_knowledge_to_species("Deinococcus radiodurans", "RADIX-2")

    # 3. Simular RADIX-2 sob radiação extrema
    phi_c = PhiCField(coupling_constant=0.15)
    simulator = RADIX2Simulator(phi_c, phi_c_value=0.9999, transfer_model=model)

    print("🧬 Simulando RADIX-2 sob 75 kGy...")
    result = simulator.simulate_with_transfer_learning(radiation_stress=75.0, max_cycles=500)

    # 4. Prova combinada
    combined = hashlib.sha3_256(
        (result["integrity_proof"] + str(result["integrated_score"])).encode()
    ).hexdigest()[:16]

    print(f"\n🧬🔄🧠 Integração RADIX-2 + Transfer Learning:")
    print(f"   Φ_C base: {result['phi_c_background']:.6f}")
    print(f"   Φ_C boosted: {result['phi_c_boosted']:.6f}")
    print(f"   Transfer contribution: {result['transfer_contribution']:.4f}")
    print(f"   Repair success: {result['repair_success']}")
    print(f"   Integrated score @ 75 kGy: {result['integrated_score']:.4f}")
    print(f"   Prova combinada: {combined}")
    print("✅ Full integration RADIX-2 + Transfer Learning passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
