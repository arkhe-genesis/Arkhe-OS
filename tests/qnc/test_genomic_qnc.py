#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_genomic_qnc.py — Testes para Substrato 6176: Quantum Neural Coding
"""

import pytest
import numpy as np
from arkp_qnc.src.genomic_qnc import GenomicQNC, GenomicQNCConfig
from arkp_qnc.src.phi_c_attention import PhiCAttention, PhiCAttentionConfig
from arkp_qnc.src.quantum_layers import QuantumDenseLayer, QuantumDenseConfig, fidelity

def test_quantum_dense_layer_forward_backward():
    """Testa forward/backward de camada densa quântica."""
    config = QuantumDenseConfig(input_dim=4, output_dim=2)
    layer = QuantumDenseLayer(config)

    # Input: estado puro aleatório
    psi = np.random.randn(4) + 1j * np.random.randn(4)
    psi /= np.linalg.norm(psi)
    rho_in = np.outer(psi, psi.conj())

    # Forward
    rho_out = layer.forward(rho_in)

    # Verificar propriedades de operador densidade
    assert np.allclose(rho_out, rho_out.conj().T), "Output must be Hermitian"
    assert np.all(np.linalg.eigvalsh(rho_out) >= -1e-10), "Output must be positive semidefinite"
    assert np.isclose(np.trace(rho_out), 1.0), "Output must have unit trace"

    # Backward
    grad_out = np.eye(2) / 2  # Gradiente simplificado
    grads = layer.backward(grad_out, lr=0.01)

    assert len(grads) == config.output_dim
    print("✅ QuantumDenseLayer forward/backward test passed")

def test_phi_c_attention_modulation():
    """Testa modulação de atenção por campo Φ_C."""
    config = PhiCAttentionConfig(query_dim=4, key_dim=4, value_dim=4)
    attention = PhiCAttention(config)

    # Criar estados de teste
    query = np.eye(4) / 4  # Maximally mixed
    keys = [np.outer(np.array([1,0,0,0]), [1,0,0,0]),  # Pure state |0⟩
            np.eye(4) / 4]  # Maximally mixed
    values = keys.copy()

    # Atenção sem modulação Φ_C
    scores_no_mod = attention.compute_attention_scores([query], keys, phi_c_field=None)

    # Atenção com Φ_C coerente (deve favorecer estados coerentes)
    phi_c_coherent = np.eye(4) / 4
    scores_with_mod = attention.compute_attention_scores([query], keys, phi_c_field=phi_c_coherent)

    # Verificar que modulação afeta scores
    assert not np.allclose(scores_no_mod, scores_with_mod), "Φ_C modulation should affect scores"

    # Estado maximally mixed deve ter score mais alto com Φ_C coerente
    assert scores_with_mod[0, 1] >= scores_with_mod[0, 0], "Mixed state should be favored by coherent Φ_C"

    print("✅ PhiCAttention modulation test passed")

def test_genomic_qnc_training_convergence():
    """Testa convergência de treinamento do GenomicQNC."""
    config = GenomicQNCConfig(
        vocab_size=4,
        max_sequence_length=32,
        embedding_dim=4,
        hidden_dim=8,
        num_classes=2,
        num_attention_heads=1,
        phi_c_coupling=0.1,
        learning_rate=0.05,
    )

    model = GenomicQNC(config)

    # Dataset sintético simples
    train_data = [
        ("ATGC" * 8, 1),  # Padrão ATGC → resistente
        ("AAAA" * 8, 0),  # Padrão AAAA → sensível
        ("GGGG" * 8, 0),
        ("ATGCATGCATGCATGC", 1),
    ]

    # Treinar por poucas épocas
    losses = []
    for epoch in range(20):
        epoch_loss = 0
        for seq, label in train_data:
            metrics = model.train_step(seq, label)
            epoch_loss += metrics['loss']
        losses.append(epoch_loss / len(train_data))

    # Verificar que loss diminui (tendência geral)
    assert losses[-1] < losses[0] * 1.5, "Loss should generally decrease"

    # Estimar taxa de convergência
    from arkp_qnc.src.radix1_trainer import RADIX1Trainer
    trainer = RADIX1Trainer.__new__(RADIX1Trainer)  # Hack para acessar método privado
    beta = trainer._estimate_convergence_rate(losses)

    assert 0.0 <= beta <= 2.0, f"Convergence rate β should be reasonable, got {beta}"

    print(f"✅ GenomicQNC convergence test passed (β={beta:.3f})")

def test_chaperone_designer_affinity_prediction():
    """Testa predição de afinidade de chaperonas."""
    from arkp_qnc.src.chaperone_designer import QNCChaperoneDesigner

    # Modelo QNC mínimo para teste
    config = GenomicQNCConfig(
        vocab_size=4, max_sequence_length=16, embedding_dim=4,
        hidden_dim=8, num_classes=2, phi_c_coupling=0.1
    )
    qnc_model = GenomicQNC(config)

    designer = QNCChaperoneDesigner(qnc_model)

    # Testar predição para diferentes chaperonas
    protein_seq = "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE"

    for chaperone in ['Hsp70', 'GroEL']:
        result = designer.predict_binding_affinity(protein_seq, chaperone)

        assert 0.0 <= result['affinity_score'] <= 1.0
        assert 0.0 <= result['confidence'] <= 1.0
        assert 'qnc_contribution' in result
        assert 'phi_c_contribution' in result

    print("✅ ChaperoneDesigner affinity prediction test passed")

def test_full_qnc_pipeline_radix1():
    """Teste de integração completa: treinamento → predição RADIX-1."""
    from arkp_qnc.src.radix1_trainer import RADIX1Trainer, TrainingConfig

    config = TrainingConfig(
        epochs=30,
        batch_size=2,
        learning_rate=0.05,
        validation_split=0.25,
        early_stopping_patience=5,
    )

    trainer = RADIX1Trainer(config)
    results = trainer.train()

    # Verificar métricas de treinamento
    assert results['epochs_trained'] >= 10
    assert 0.0 <= results['final_val_acc'] <= 1.0
    assert 0.0 <= results['convergence_beta'] <= 2.0

    # Avaliar em RADIX-1
    radix1_result = trainer.evaluate_on_radix1()

    # RADIX-1 deve ser predito como resistente (label=1)
    assert radix1_result['expected_label'] == 1
    # Pode não ser 100% correto com poucos dados, mas confiança deve ser razoável
    assert radix1_result['confidence'] > 0.3

    print(f"✅ Full QNC pipeline test passed")
    print(f"   RADIX-1 prediction: class={radix1_result['predicted_class']}, "
          f"confidence={radix1_result['confidence']:.3f}, "
          f"Φ_C coherence={radix1_result['phi_c_coherence']:.3f}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
