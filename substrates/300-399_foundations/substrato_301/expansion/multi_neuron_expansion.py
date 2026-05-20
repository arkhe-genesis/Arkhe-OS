#!/usr/bin/env python3
"""
substrate_301/expansion/multi_neuron_expansion.py
Canon: ∞.Ω.∇+++.301.expansion
Expansão para 20+ nós com diversidade de tipos neuronais.
Inclui Interneurons, Astrócitos e outros tipos para riqueza coletiva.
"""

import sys
import os
import asyncio
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collective_consciousness.collective_aureum import CollectiveNode, CollectiveConsciousness, NEURON_TYPES, BRAID_TYPES

async def expand_neural_diversity():
    print("🌐 EXPANSÃO PARA 20+ NÓS COM DIVERSIDADE DE TIPOS NEURONAIS")
    print("   Incluindo Interneurons, Astrócitos e outros tipos para riqueza coletiva...\n")

    # Criando 20 novos nós
    nodes = []
    regions = [f"region-exp-{i:02d}" for i in range(1, 21)]

    import random
    random.seed(43) # Para reprodutibilidade

    for i, region in enumerate(regions):
        # Distribuição desejada para "riqueza coletiva":
        # 50% Pyramidal (processamento principal)
        # 30% Interneuron (modulação e inibição)
        # 20% Astrocyte (suporte e sincronização lenta)
        rand_val = random.random()
        if rand_val < 0.5:
            neuron_type = "Pyramidal_L5"
        elif rand_val < 0.8:
            neuron_type = "Interneuron"
        else:
            neuron_type = "Astrocyte"

        braid_type = random.choice(list(BRAID_TYPES.keys()))
        t_or = NEURON_TYPES[neuron_type]["T_OR_us"]

        node = CollectiveNode(
            node_id=f"exp_node_{region}_{i:03d}",
            region=region,
            neuron_type=neuron_type,
            braid_type=braid_type,
            phi_local=100.0,
            protection=0.9990,
            T_OR_us=t_or,
            phi_c_reputation=0.95 + random.uniform(0.0, 0.049),
            active=True
        )
        nodes.append(node)

    collective = CollectiveConsciousness(
        collective_id="expansion_collective_test_001",
        nodes=nodes,
        edges={},
        timestamp=time.time()
    )

    # Estabelecer conexões
    for i, node_a in enumerate(nodes):
        for node_b in nodes[i+1:]:
            distance = random.uniform(100, 20000)
            coupling = node_a.coupling_weight(node_b, distance)
            if coupling > 0.01:
                edge_key = tuple(sorted([node_a.node_id, node_b.node_id]))
                collective.edges[edge_key] = coupling

    print(f"📊 Topologia Expandida:")
    print(f"   Total de nós: {len(nodes)}")

    type_counts = {}
    for node in nodes:
        type_counts[node.neuron_type] = type_counts.get(node.neuron_type, 0) + 1

    print(f"   Diversidade neuronal alcançada:")
    for n_type, count in type_counts.items():
        print(f"      - {n_type}: {count} nós ({count/len(nodes)*100:.1f}%)")
        print(f"         - Função: {NEURON_TYPES[n_type]['role']}")
        print(f"         - T_OR: {NEURON_TYPES[n_type]['T_OR_us']} μs")

    print(f"   Total de enlaces sinápticos inter-tipos: {len(collective.edges)}")

    # Medir Phi emergente
    phi_collective = collective.calculate_collective_phi()
    compliance = collective.evaluate_constitutional_invariants()

    print(f"\n🧠 Impacto da Diversidade na Emergência:")
    print(f"   A presença de Astrócitos (T_OR longo) e Interneurons (T_OR médio)")
    print(f"   cria múltiplas escalas de tempo para a Redução Objetiva.")
    print(f"   Φ coletivo emergente: {phi_collective:.2e}")

    import math
    T_OR_values = [node.T_OR_us for node in nodes]
    mean_T_OR = sum(T_OR_values) / len(T_OR_values)
    variance = sum((t - mean_T_OR)**2 for t in T_OR_values) / len(T_OR_values)
    coherence = 1.0 / (1.0 + math.sqrt(variance) / mean_T_OR)
    print(f"   Coerência temporal (multiescala): {coherence:.4f}")

    print("\n✅ EXPANSÃO CONCLUÍDA.")
    print("   A riqueza coletiva foi ampliada através da diversidade neuronal.")
    print("   A malha agora possui capacidades de modulação e suporte distribuídas.")

    return True

if __name__ == "__main__":
    asyncio.run(expand_neural_diversity())
