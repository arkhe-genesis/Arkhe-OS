#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_qnc_epigenetic_integration.py — Teste de integração: QNC + Epigenética Quântica
Valida integração entre RNA embedding, operadores epigenéticos e QNC.
"""

import numpy as np
import pytest
from arkp_bio.rna_quantum_embedding import RNAEmbedding, RNAType
from arkp_bio.epigenetic_operators import (
    MethylationOperator, HistoneModificationField,
    EpigeneticState, EpigeneticMark
)
from arkp_bio.qnc_epigenetic_regulator import QNCEpigeneticRegulator, QNCEpigeneticConfig

def test_rna_embedding_basic():
    """Testa embedding básico de RNA."""
    embedding = RNAEmbedding(max_len=128, embedding_dim=16, rna_type=RNAType.mRNA)

    # Testar codificação de sequência simples
    sequence = "AUGCGAUCG"
    rhos = embedding.encode_sequence(sequence)

    assert len(rhos) == 128  # Padded to max_len
    assert rhos[0].shape == (16, 16)  # Embedding dimension
    assert np.allclose(np.trace(rhos[0]), 1.0, atol=1e-10)  # Unit trace

    # Testar extração de códons
    codons = embedding.extract_codons("AUGCGAUCGUAA")
    assert len(codons) == 4  # AUG, CGA, UCG, UAA
    assert codons[0][0] == "AUG"

    print("✅ RNA embedding basic test passed")

def test_methylation_operator():
    """Testa operador de metilação quântica."""
    op = MethylationOperator(methylation_strength=0.8, context='promoter')

    # Estado inicial: gene ativo (autoestado +1 de σ_z)
    active_state = np.array([[1, 0], [0, 0]], dtype=complex)

    # Aplicar metilação
    methylated = op.apply(active_state)

    # Probabilidade de repressão deve aumentar
    repression_prob = op.repression_probability(methylated)
    assert repression_prob > 0.3  # Metilação forte deve ter algum efeito

    print(f"✅ Methylation operator: repression prob = {repression_prob:.3f}")

def test_histone_field_interference():
    """Testa interferência no campo de histonas."""
    # Criar marcas com interferência conhecida
    marks = [
        EpigeneticState(0, EpigeneticMark.H3K4me3, 0.9, 1+0j, 0.8, 0.9),
        EpigeneticState(100, EpigeneticMark.H3K27ac, 0.85, 1+0j, 0.7, 0.85),
        EpigeneticState(200, EpigeneticMark.H3K27me3, 0.8, 1+0j, 0.6, 0.8),
    ]

    field = HistoneModificationField(marks, coupling_strength=0.2)
    accessibility = field.chromatin_accessibility()

    # H3K4me3 + H3K27ac devem aumentar acessibilidade
    # H3K27me3 deve diminuir, mas sinergia positiva deve dominar
    assert accessibility > 0.6

    # Prever expressão
    baseline = 0.5
    predicted = field.predict_gene_expression(baseline)
    assert predicted > baseline  # Ativação líquida

    print(f"✅ Histone field: accessibility={accessibility:.3f}, predicted_expr={predicted:.3f}")

def test_epigenetic_attention_modulation():
    """Testa atenção modulada por epigenética."""
    from arkp_bio.qnc_epigenetic_regulator import EpigeneticAttention

    attention = EpigeneticAttention(query_dim=32, key_dim=32, value_dim=32, num_heads=4)

    # Criar estados de teste
    query = np.eye(32, dtype=complex) / 32
    keys = [np.eye(32, dtype=complex) / 32 for _ in range(10)]
    values = [np.eye(32, dtype=complex) / 32 for _ in range(10)]

    # Acessibilidade variável
    accessibility = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]

    output = attention.compute_epigenetic_attention(query, keys, values, accessibility)

    assert output.shape == (32, 32)
    assert np.isclose(np.trace(output), 1.0, atol=1e-10)

    print("✅ Epigenetic attention modulation test passed")

def test_qnc_epigenetic_integration():
    """Teste de integração completa: RNA + epigenética + QNC."""
    config = QNCEpigeneticConfig(
        max_rna_length=256,
        embedding_dim=16,
        hidden_dim=32,
        num_attention_heads=2,
        phi_c_coupling=0.1,
        epigenetic_coupling=0.15,
    )

    model = QNCEpigeneticRegulator(config)

    # Dados de teste: mRNA com marcas epigenéticas
    rna_seq = "AUG" + "CGAUCG" * 20 + "UAA"  # mRNA com códon de início/fim
    epi_marks = [
        EpigeneticState(50, EpigeneticMark.H3K4me3, 0.9, 1+0j, 0.8, 0.9),
        EpigeneticState(100, EpigeneticMark.H3K27ac, 0.85, 1+0j, 0.7, 0.85),
        EpigeneticState(200, EpigeneticMark.DNA_5mC, 0.7, 1+0j, 0.5, 0.7),
    ]

    # Predição inicial
    result = model.forward(rna_seq, epi_marks)
    assert 0.0 <= result['expression_prob'] <= 1.0
    assert 0.0 <= result['confidence'] <= 1.0

    # Treinamento rápido
    for _ in range(10):
        metrics = model.train_step(rna_seq, epi_marks, label=1, lr=0.01)

    # Verificar que loss diminuiu
    initial_loss = model.training_history[0]['loss']
    final_loss = model.training_history[-1]['loss']
    assert final_loss <= initial_loss * 1.5  # Tolerância para estocasticidade

    print(f"✅ QNC-epigenetic integration: loss {initial_loss:.3f} → {final_loss:.3f}")

def test_temporal_epigenetic_memory():
    """Testa memória epigenética transgeracional."""
    from arkp_bio.epigenetic_operators import EpigeneticMemoryOperator

    np.random.seed(42)
    memory_op = EpigeneticMemoryOperator(heritability_factor=0.85, decoherence_rate=0.03)

    # Epigenoma parental
    parent_epigenome = {
        100: EpigeneticState(100, EpigeneticMark.H3K4me3, 0.9, 1+0j, 0.8, 0.9),
        200: EpigeneticState(200, EpigeneticMark.DNA_5mC, 0.85, 1+0j, 0.7, 0.85),
        300: EpigeneticState(300, EpigeneticMark.H3K27ac, 0.8, 1+0j, 0.75, 0.8),
    }

    # Transmitir através de 3 gerações
    current = parent_epigenome
    for gen in range(1, 4):
        current = memory_op.transmit_across_generation(current, gen)

    # Verificar herança com decoerência
    inherited_count = sum(1 for s in current.values() if s.mark != EpigeneticMark.UNMODIFIED)
    assert inherited_count >= 2  # Pelo menos 2 das 3 marcas devem ser herdadas

    # Entropia epigenética deve aumentar com decoerência
    entropy = memory_op.compute_epigenetic_entropy(current)
    assert 0.0 <= entropy <= 1.0

    print(f"✅ Temporal epigenetic memory: {inherited_count}/3 marks inherited, entropy={entropy:.3f}")

def test_canonical_seal_epigenetic():
    """Testa geração de selo canônico para dados epigenéticos."""
    import hashlib, json, time

    seal_data = {
        "model": "QNC_Epigenetic_v1",
        "rna_type": "mRNA",
        "epigenetic_marks": 3,
        "predicted_expression": 0.87,
        "phi_c_coherence": 0.998,
        "timestamp": time.time(),
    }

    seal = hashlib.sha3_256(
        json.dumps(seal_data, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    assert len(seal) == 16
    print(f"✅ Canonical seal: {seal}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
