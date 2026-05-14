#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radix2_epigenetic_demo.py — Demonstração: Regulação epigenética do genoma RADIX‑2
"""

import numpy as np
from arkp_bio.qnc_epigenetic_regulator import QNCEpigeneticRegulator, QNCEpigeneticConfig
from arkp_bio.epigenetic_operators import EpigeneticState, EpigeneticMark
from arkp_bio.rna_quantum_embedding import RNAType

def run_epigenetic_demo():
    print("🧬⚛️ ARKHE Ω‑TEMP v6.5.0 — RADIX‑2 Epigenetic Regulation Demo")
    print("=" * 75)

    # 1. Configurar modelo
    print("\n[1/4] Configurando regulador QNC-epigenético...")
    config = QNCEpigeneticConfig(
        max_rna_length=512,
        embedding_dim=32,
        hidden_dim=64,
        num_attention_heads=4,
        phi_c_coupling=0.15,
        epigenetic_coupling=0.2,
    )
    regulator = QNCEpigeneticRegulator(config)

    # 2. Definir região promotora de RADIX‑2 com marcas epigenéticas
    print("\n[2/4] Definindo marcas epigenéticas no promotor de RADIX‑2...")

    # Cenário 1: Promotor ativo (alta expressão)
    active_marks = [
        EpigeneticState(100, EpigeneticMark.H3K4me3, 0.95, 1+0j, 0.9, 0.95),
        EpigeneticState(150, EpigeneticMark.H3K27ac, 0.9, 1+0j, 0.85, 0.9),
        EpigeneticState(200, EpigeneticMark.H3K36me3, 0.85, 1+0j, 0.8, 0.85),
    ]

    # Cenário 2: Promotor reprimido (baixa expressão)
    repressed_marks = [
        EpigeneticState(100, EpigeneticMark.H3K27me3, 0.9, 1+0j, 0.85, 0.9),
        EpigeneticState(150, EpigeneticMark.H3K9me3, 0.85, 1+0j, 0.8, 0.85),
        EpigeneticState(200, EpigeneticMark.DNA_5mC, 0.8, 1+0j, 0.7, 0.8),
    ]

    # Sequência de mRNA do módulo repair_executor de RADIX‑2
    radix2_mrna = "AUG" + "GCUAGC" * 80 + "UAA"  # Simulado

    # 3. Predizer expressão em diferentes cenários epigenéticos
    print("\n[3/4] Predizendo expressão de RADIX‑2 sob diferentes estados epigenéticos...")

    # Cenário ativo
    active_result = regulator.forward(radix2_mrna, active_marks, baseline_expression=0.6)
    print(f"   🔵 Promotor ATIVO:")
    print(f"      • Prob. expressão: {active_result['expression_prob']:.3f}")
    print(f"      • Confiança: {active_result['confidence']:.3f}")
    print(f"      • Acessibilidade epigenética: {active_result['epigenetic_accessibility']:.3f}")

    # Cenário reprimido
    repressed_result = regulator.forward(radix2_mrna, repressed_marks, baseline_expression=0.6)
    print(f"   🔴 Promotor REPRIMIDO:")
    print(f"      • Prob. expressão: {repressed_result['expression_prob']:.3f}")
    print(f"      • Confiança: {repressed_result['confidence']:.3f}")
    print(f"      • Acessibilidade epigenética: {repressed_result['epigenetic_accessibility']:.3f}")

    # Diferença devido à epigenética
    expression_delta = active_result['expression_prob'] - repressed_result['expression_prob']
    print(f"   📊 Δ Expressão (epigenética): {expression_delta:+.3f}")

    # 4. Simular dinâmica temporal: memória epigenética
    print("\n[4/4] Simulando herança epigenética através de divisões celulares...")
    from arkp_bio.epigenetic_operators import EpigeneticMemoryOperator

    memory_op = EpigeneticMemoryOperator(heritability_factor=0.9, decoherence_rate=0.02)

    # Epigenoma inicial (ativo)
    current_marks = {m.position: m for m in active_marks}

    print("   Geração | H3K4me3 | H3K27ac | H3K36me3 | Acessibilidade")
    print("   " + "-" * 55)

    for gen in range(5):
        # Calcular acessibilidade atual
        marks_list = list(current_marks.values())
        accessibility = np.mean([
            0.9 if m.mark in {EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac, EpigeneticMark.H3K36me3}
            else 0.3 if m.mark in {EpigeneticMark.H3K27me3, EpigeneticMark.H3K9me3, EpigeneticMark.DNA_5mC}
            else 0.5
            for m in marks_list
        ])

        # Contar marcas ativas
        active_count = sum(1 for m in marks_list if m.mark in {
            EpigeneticMark.H3K4me3, EpigeneticMark.H3K27ac, EpigeneticMark.H3K36me3
        })

        print(f"   {gen:7d} | {active_count:7d}   |   {active_count:7d}   |   {active_count:8d}   | {accessibility:12.3f}")

        # Transmitir para próxima geração
        current_marks = memory_op.transmit_across_generation(current_marks, gen + 1)

    # Selo canônico
    import hashlib, json, time
    seal_data = {
        "demo": "RADIX2_Epigenetic",
        "active_expression": active_result['expression_prob'],
        "repressed_expression": repressed_result['expression_prob'],
        "epigenetic_delta": expression_delta,
        "timestamp": time.time(),
    }
    seal = hashlib.sha3_256(json.dumps(seal_data, sort_keys=True, default=str).encode()).hexdigest()[:16]

    print(f"\n🔐 Selo canônico: {seal}")
    print(f"\n✨ Demo concluída — Regulação epigenética de RADIX‑2 simulada!")

if __name__ == "__main__":
    run_epigenetic_demo()
