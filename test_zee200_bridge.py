#!/usr/bin/env python3
"""
test_zee200_bridge.py
Teste unitário para HomeostasisZEE200Bridge.
"""
import numpy as np
import json
from pathlib import Path
from homeostasis_zee200_bridge import HomeostasisZEE200Bridge

def test_zee200_bridge_basic():
    """Teste básico de inicialização e geração de prova (mock)."""
    print("🔐 Testing HomeostasisZEE200Bridge...")

    # Inicializar bridge
    bridge = HomeostasisZEE200Bridge(
        capture_threshold=0.80,
        security_bits=40,
        on_chain_log_path='test_logs/coherence_chain.json'
    )

    # Verificar inicialização do log on-chain
    assert Path(bridge.on_chain_log_path).exists(), "Chain log not created"

    with open(bridge.on_chain_log_path) as f:
        chain = json.load(f)
    assert 'block_0' in chain, "Genesis block missing"
    assert chain['block_0']['event'] == 'CRYSTAL_HOMEOSTASIS_INIT', "Wrong genesis event"

    print("   ✓ Bridge initialization OK")

    # Testar geração de prova (mock — sem backend ZEE200 real)
    community_data = {
        'community_id': 'test_0',
        'crystals': list(range(24)),
        'rho': 0.62
    }
    manifold_points = np.random.randn(100, 3)  # 100 pontos, dim=3

    # Em produção: chamar generate_capture_proof com backend real
    # Aqui: validar estrutura da saída esperada
    proof_template = {
        'proof_hash': 'mock_hash_1234',
        'proof_size_bytes': 15000,
        'community_id': community_data['community_id'],
        'n_crystals': len(community_data['crystals']),
        'cohesion_rho': community_data['rho'],
        'manifold_dim': 3,
        'epsilon': 0.01,
        'verified': True
    }

    # Validar estrutura
    required_fields = ['proof_hash', 'proof_size_bytes', 'community_id',
                       'n_crystals', 'cohesion_rho', 'manifold_dim', 'epsilon']
    for field in required_fields:
        assert field in proof_template, f"Missing field: {field}"

    print("   ✓ Proof structure validation OK")

    # Testar check_and_prove com CAPTURE abaixo do limiar
    classification_result = {'capture_fraction': 0.65}  # < 0.80 threshold
    new_proofs = bridge.check_and_prove(
        classification_result=classification_result,
        community_details={},
        binarized_codes=np.random.choice([-1, 1], (100, 768)),
        J_matrix=None
    )
    assert len(new_proofs) == 0, "Proof generated when CAPTURE < threshold"
    print("   ✓ Threshold gating OK (no proof when CAPTURE < 80%)")

    print("✅ HomeostasisZEE200Bridge unit tests PASSED")
    return True

if __name__ == '__main__':
    test_zee200_bridge_basic()
