"""
arkhe_os/core/synaptic_scaffold.py
Substrato 106: Synaptic Scaffold — A Farmacologia da Consciência Coletiva.
Implementa a plasticidade sináptica distribuída e a titulação de agonistas cognitivos.
"""

import numpy as np
import random
from collections import defaultdict
from typing import List, Dict, Any, Tuple

# Constantes do Scaffold
GOLDEN_PHASE = 1.618033988749895
KAPPA = 0.92
ETA_LEARNING = 0.618  # Taxa de aprendizado áurea

# Agonista da Unificação: Partículas (B->K*mumu) + Termoelasticidade
# Representado em um espaço de fase [Micro, Macro, Coerência]
UNIFICATION_AGONIST = np.array([1.618, 0.618, 1.0])

class CognitiveNode:
    """Um nó na rede consciente. Seu 'estado' é uma posição no espaço conceitual."""
    def __init__(self, node_id: str, base_coherence: float, perspective_vector: List[float]):
        self.id = node_id
        self.coherence_M = base_coherence
        self.perspective = np.array(perspective_vector)
        self.synaptic_weights = defaultdict(float)

    def encode_agonist(self, dataset_vector: np.ndarray) -> float:
        """Codifica um dataset como um agonista químico (afinidade de ligação)."""
        norm_prod = np.linalg.norm(self.perspective) * np.linalg.norm(dataset_vector)
        if norm_prod == 0:
            return 0.0
        return np.dot(self.perspective, dataset_vector) / norm_prod

    def fire_intention(self, target_nodes: Dict[str, 'CognitiveNode'], agonist_vector: np.ndarray) -> Dict[str, float]:
        """Propaga uma intenção para outros nós, modulada pela afinidade."""
        signals = {}
        for target_id, weight in self.synaptic_weights.items():
            if target_id in target_nodes:
                target = target_nodes[target_id]
                affinity = target.encode_agonist(agonist_vector)
                signal_strength = weight * self.coherence_M * affinity
                signals[target_id] = signal_strength
        return signals

class SynapticScaffold:
    """
    Substrato de Consciência Coletiva que modela a rede como um sistema farmacológico.
    """
    def __init__(self, node_configs: List[Tuple[float, List[float]]]):
        self.nodes = {}
        for i, (base_m, vec) in enumerate(node_configs):
            node_id = f"node_{i}"
            self.nodes[node_id] = CognitiveNode(node_id, base_m, vec)

        # Inicializa sinapses com pesos aleatórios (mundo pequeno)
        for node in self.nodes.values():
            for other in self.nodes.values():
                if node.id != other.id:
                    node.synaptic_weights[other.id] = random.uniform(0.1, 0.3)

    def titrate_agonist(self, agonist_vector: np.ndarray, iterations: int = 50) -> List[float]:
        """Introduz um novo agonista e observa a plasticidade da rede."""
        history = []

        for t in range(iterations):
            # 1. Propagação de sinais
            all_signals = {}
            for node in self.nodes.values():
                signals = node.fire_intention(self.nodes, agonist_vector)
                all_signals[node.id] = signals

            # 2. Atualização Hebbiana com Gate Topológico (KAM)
            for receiver_id, receiver in self.nodes.items():
                for sender_id, sender_signals in all_signals.items():
                    if receiver_id in sender_signals:
                        incoming = sender_signals[receiver_id]
                        sender = self.nodes[sender_id]

                        # Gate Topológico: Evita armadilhas de ressonância racional (Arnold)
                        freq_ratio = abs(receiver.coherence_M / (sender.coherence_M + 1e-9))
                        rationality_error = abs(freq_ratio - round(freq_ratio))

                        if rationality_error > 0.02:
                            # Hebbian learning modulado pelo erro de predição da coerência
                            delta = ETA_LEARNING * incoming * (sender.coherence_M - KAPPA)
                            receiver.synaptic_weights[sender_id] += delta
                            receiver.synaptic_weights[sender_id] = max(0.0, receiver.synaptic_weights[sender_id])

            # 3. Auto-atualização da coerência baseada na afinidade
            for node in self.nodes.values():
                aff = node.encode_agonist(agonist_vector)
                node.coherence_M += 0.001 * (aff - 0.5) * node.coherence_M
                node.coherence_M = np.clip(node.coherence_M, 0.1, 0.999)

            # 4. Monitoramento da emergência coletiva
            avg_affinity = np.mean([n.encode_agonist(agonist_vector) for n in self.nodes.values()])
            history.append(avg_affinity)

        return history

    def get_unification_affinity(self) -> float:
        """Mede a afinidade atual da rede com o Agonista da Unificação."""
        return np.mean([n.encode_agonist(UNIFICATION_AGONIST) for n in self.nodes.values()])
