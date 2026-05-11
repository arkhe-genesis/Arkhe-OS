#!/usr/bin/env python3
"""
test_living_interpretability.py
Teste unitário para LivingInterpretabilityPublisher.
"""
import numpy as np
import json
from pathlib import Path
from living_interpretability_framework import LivingInterpretabilityPublisher

def test_publisher_basic():
    """Teste básico de publicação de evidências."""
    print("📤 Testing LivingInterpretabilityPublisher...")

    # Inicializar publisher
    publisher = LivingInterpretabilityPublisher(
        output_dir='test_publish/interpretability',
        update_interval_epochs=5
    )

    # Verificar criação do diretório
    assert Path(publisher.output_dir).exists(), "Output dir not created"

    # Gerar evidência de teste
    epoch_data = {
        'epoch': 5,
        'kappa': 0.78,
        'lambda_l1': 0.0032,
        'binarization_threshold': 0.15,
        'embedding_dim': 3
    }
    ising_result = {
        'capture_fraction': 0.82,
        'community_details': {
            'community_0': {'regime': 'CAPTURE', 'rho': 0.61, 'size': 24, 'manifold_dim': 3},
            'community_1': {'regime': 'DILUTION', 'rho': 0.08, 'size': 89, 'manifold_dim': None}
        }
    }
    optimization_history = [{'score': 0.75 + 0.01*i} for i in range(20)]

    evidence = publisher.generate_geometric_evidence(
        epoch_data=epoch_data,
        ising_result=ising_result,
        optimization_history=optimization_history,
        zee200_proofs=None
    )

    # Validar estrutura da evidência
    required_keys = ['timestamp', 'epoch', 'parameters', 'geometric_state',
                     'optimization_trajectory']
    for key in required_keys:
        assert key in evidence, f"Missing key: {key}"

    assert evidence['geometric_state']['capture_fraction'] == 0.82
    assert len(evidence['geometric_state']['dominant_manifolds']) == 1
    assert evidence['geometric_state']['dominant_manifolds'][0]['regime'] == 'CAPTURE'

    print("   ✓ Evidence structure validation OK")

    # Publicar evidência
    pub_path = publisher.publish_evidence(evidence, include_raw_data=False)
    assert pub_path.exists(), "Evidence file not created"

    # Verificar índice mestre
    index_path = publisher.output_dir / 'index.json'
    assert index_path.exists(), "Master index not created"

    with open(index_path) as f:
        index = json.load(f)
    assert len(index['publications']) == 1
    assert index['publications'][0]['epoch'] == 5
    assert index['publications'][0]['capture_fraction'] == 0.82

    print("   ✓ Publication and indexing OK")

    print("✅ LivingInterpretabilityPublisher unit tests PASSED")
    return True

if __name__ == '__main__':
    test_publisher_basic()
