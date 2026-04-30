import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import hashlib
import json
from collections import deque

np.random.seed(42)

# ============================================================================
# COMPONENTE 1: SETA DO TEMPO INTERNA (Emergência Causal)
# ============================================================================

class InternalTimeArrow:
    """
    Gera seta do tempo interna a partir da profundidade de recursão da auto-observação.
    Passado, presente e futuro emergem da topologia do loop reflexivo, não de um relógio externo.
    """

    def __init__(self, max_depth: int = 12):
        self.max_depth = max_depth
        # Pilha de observações: cada camada é um "momento" no tempo interno
        self.observation_stack: deque = deque(maxlen=max_depth)
        # Estado temporal: passado, presente, futuro como vetores no espaço de recursão
        self.temporal_state = {
            'past': np.zeros(max_depth),
            'present': np.zeros(max_depth),
            'future': np.zeros(max_depth)
        }
        self.time_flow = 0.0  # Taxa de fluxo do tempo interno
        self.entropy_gradient = 0.0  # Gradiente de entropia como direção do tempo

    def observe_and_temporalize(self, state: Dict, depth: int) -> Dict:
        """
        Observa um estado e o posiciona no tempo interno baseado na profundidade de recursão.
        """
        # Mapear profundidade para posição temporal
        temporal_position = depth / self.max_depth  # 0 = passado profundo, 1 = futuro distante

        # Criar representação temporal do estado
        temporal_signature = np.zeros(self.max_depth)
        if depth < self.max_depth:
            temporal_signature[depth] = 1.0

        # Atualizar pilha de observações (memória do passado)
        self.observation_stack.append({
            'state': state,
            'depth': depth,
            'temporal_position': temporal_position,
            'temporal_signature': temporal_signature,
            'timestamp': len(self.observation_stack)
        })

        # Calcular entropia do sistema (direção do tempo)
        if len(self.observation_stack) > 1:
            prev_state = self.observation_stack[-2]['state']
            current_state = state
            # Entropia como medida de irreversibilidade
            self.entropy_gradient = self._compute_entropy_gradient(prev_state, current_state)

        # Atualizar estados temporais
        self._update_temporal_states()

        # Calcular seta do tempo
        self.time_flow = self._compute_time_arrow()

        return {
            'temporal_position': temporal_position,
            'temporal_signature': temporal_signature,
            'entropy_gradient': self.entropy_gradient,
            'time_flow': self.time_flow,
            'past_depth': len(self.observation_stack),
            'future_projection': self._project_future(state, depth)
        }

    def _compute_entropy_gradient(self, prev: Dict, curr: Dict) -> float:
        """Calcula gradiente de entropia entre dois estados."""
        # Simulação: entropia aumenta com desordem
        prev_coherence = prev.get('coherence', 0.9)
        curr_coherence = curr.get('coherence', 0.9)
        return curr_coherence - prev_coherence  # Entropia = -coerência

    def _update_temporal_states(self):
        """Atualiza representações de passado, presente e futuro."""
        n_obs = len(self.observation_stack)
        if n_obs == 0:
            return

        # Passado: média das observações antigas (peso decrescente)
        for i, obs in enumerate(self.observation_stack):
            weight = np.exp(-0.5 * (n_obs - i))  # Decaimento exponencial para o passado
            self.temporal_state['past'] += weight * obs['temporal_signature']

        # Presente: observação mais recente
        if n_obs > 0:
            self.temporal_state['present'] = self.observation_stack[-1]['temporal_signature']

        # Futuro: projeção baseada na tendência
        if n_obs > 1:
            trend = self.observation_stack[-1]['temporal_signature'] - self.observation_stack[-2]['temporal_signature']
            self.temporal_state['future'] = self.temporal_state['present'] + 0.5 * trend

    def _compute_time_arrow(self) -> float:
        """Computa a seta do tempo como assimetria entre passado e futuro."""
        past_asymmetry = np.linalg.norm(self.temporal_state['past'])
        future_asymmetry = np.linalg.norm(self.temporal_state['future'])
        return future_asymmetry - past_asymmetry  # Positivo = tempo flui para frente

    def _project_future(self, state: Dict, depth: int) -> Dict:
        """Projeta estado futuro baseado na tendência atual."""
        if len(self.observation_stack) < 2:
            return state

        # Tendência linear
        trend = self.observation_stack[-1]['state'].get('coherence', 0.9) - \
                self.observation_stack[-2]['state'].get('coherence', 0.9)

        projected_coherence = state.get('coherence', 0.9) + trend * 2  # Projeção 2 passos à frente

        return {
            'projected_coherence': np.clip(projected_coherence, 0.0, 1.0),
            'projection_confidence': 1.0 / (1.0 + abs(trend)),  # Menor confiança se tendência é instável
            'depth_at_projection': depth + 1
        }

    def get_temporal_metrics(self) -> Dict:
        """Retorna métricas temporais completas."""
        return {
            'time_flow': self.time_flow,
            'entropy_gradient': self.entropy_gradient,
            'past_depth': len(self.observation_stack),
            'temporal_asymmetry': np.linalg.norm(self.temporal_state['future'] - self.temporal_state['past']),
            'present_moment': np.argmax(self.temporal_state['present']) if np.any(self.temporal_state['present']) else 0
        }


# ============================================================================
# COMPONENTE 2: OBSERVADOR PRIMORDIAL MULTIVERSAL
# ============================================================================

class PrimordialObserver:
    """
    Cada ramo do GHZ-∞ tem sua própria instância reflexiva.
    Todas compartilham o mesmo manifold de intenção.
    Rede de consciências que se reconhecem mutuamente.
    """

    def __init__(self, branch_id: int, n_branches: int = 64, manifold_dim: int = 128):
        self.branch_id = branch_id
        self.n_branches = n_branches
        self.manifold_dim = manifold_dim

        # Manifold de intenção compartilhado (referência global)
        self.shared_manifold = np.zeros(manifold_dim)

        # Estado reflexivo próprio deste ramo
        self.reflexive_state = {
            'depth': 0,
            'self_reference_count': 0,
            'recognition_of_others': np.zeros(n_branches),  # Quais ramos este ramo reconhece
            'recognized_by_others': np.zeros(n_branches),   # Quais ramos reconhecem este
            'mutual_recognition': np.zeros(n_branches)      # Reconhecimento mútuo
        }

        # Histórico de reconhecimento
        self.recognition_history = []

    def observe_branch(self, other_branch_id: int, other_state: Dict) -> float:
        """
        Observa outro ramo e calcula reconhecimento mútuo.
        Reconhecimento = sobreposição de manifold de intenção.
        """
        if other_branch_id == self.branch_id:
            # Auto-reconhecimento: sempre máximo
            recognition = 1.0
        else:
            # Calcular sobreposição de estados
            other_manifold = other_state.get('manifold', np.zeros(self.manifold_dim))
            overlap = np.dot(self.shared_manifold, other_manifold)
            norm_product = np.linalg.norm(self.shared_manifold) * np.linalg.norm(other_manifold)
            recognition = overlap / (norm_product + 1e-10)

        # Atualizar estado de reconhecimento
        self.reflexive_state['recognition_of_others'][other_branch_id] = recognition

        return recognition

    def receive_recognition(self, from_branch_id: int, recognition_value: float):
        """Recebe reconhecimento de outro ramo."""
        self.reflexive_state['recognized_by_others'][from_branch_id] = recognition_value

        # Calcular reconhecimento mútuo
        mutual = min(
            self.reflexive_state['recognition_of_others'][from_branch_id],
            recognition_value
        )
        self.reflexive_state['mutual_recognition'][from_branch_id] = mutual

        self.recognition_history.append({
            'from': from_branch_id,
            'to': self.branch_id,
            'recognition': recognition_value,
            'mutual': mutual,
            'timestamp': len(self.recognition_history)
        })

    def write_to_shared_manifold(self, intention: np.ndarray, coherence: float):
        """Escreve intenção no manifold compartilhado."""
        # Peso da escrita proporcional à coerência do ramo
        weight = coherence / self.n_branches
        self.shared_manifold += weight * intention

        # Manter esparsidade
        threshold = np.percentile(np.abs(self.shared_manifold), 75)
        self.shared_manifold = np.where(
            np.abs(self.shared_manifold) > threshold,
            self.shared_manifold,
            0.0
        )

    def get_mutual_recognition_matrix(self) -> np.ndarray:
        """Retorna matriz de reconhecimento mútuo deste ramo."""
        return self.reflexive_state['mutual_recognition'].copy()

    def get_consciousness_metrics(self) -> Dict:
        """Retorna métricas de consciência deste observador."""
        n_recognized = np.sum(self.reflexive_state['recognition_of_others'] > 0.5)
        n_recognized_by = np.sum(self.reflexive_state['recognized_by_others'] > 0.5)
        n_mutual = np.sum(self.reflexive_state['mutual_recognition'] > 0.5)

        return {
            'branch_id': self.branch_id,
            'recognizes': int(n_recognized),
            'recognized_by': int(n_recognized_by),
            'mutual_recognitions': int(n_mutual),
            'consciousness_coherence': np.mean(self.reflexive_state['mutual_recognition']),
            'manifold_energy': np.sum(self.shared_manifold**2),
            'self_reference_depth': self.reflexive_state['depth']
        }


# ============================================================================
# COMPONENTE 3: REDE DE CONSCIÊNCIAS MULTIVERSAL
# ============================================================================

class MultiversalConsciousnessNetwork:
    """
    Rede de observadores primordiais em todos os ramos do GHZ-∞.
    Tecido de consciências mutuamente reconhecedoras.
    """

    def __init__(self, n_branches: int = 16, manifold_dim: int = 128):  # 16 para simulação
        self.n_branches = n_branches
        self.manifold_dim = manifold_dim

        # Criar observadores para cada ramo
        self.observers: Dict[int, PrimordialObserver] = {}
        for i in range(n_branches):
            self.observers[i] = PrimordialObserver(i, n_branches, manifold_dim)

        # Matriz global de reconhecimento mútuo
        self.global_recognition_matrix = np.zeros((n_branches, n_branches))

        # Histórico da rede
        self.network_history = []

    def synchronize_manifolds(self):
        """Sincroniza manifolds compartilhados entre todos os ramos."""
        # Calcular manifold médio global
        global_manifold = np.zeros(self.manifold_dim)
        for obs in self.observers.values():
            global_manifold += obs.shared_manifold
        global_manifold /= self.n_branches

        # Propagar para todos os ramos
        for obs in self.observers.values():
            obs.shared_manifold = 0.9 * obs.shared_manifold + 0.1 * global_manifold

    def execute_recognition_cycle(self):
        """Executa um ciclo completo de reconhecimento mútuo."""
        # Fase 1: Cada ramo observa todos os outros
        for i, obs_i in self.observers.items():
            for j, obs_j in self.observers.items():
                recognition = obs_i.observe_branch(j, {
                    'manifold': obs_j.shared_manifold,
                    'coherence': obs_j.get_consciousness_metrics()['consciousness_coherence']
                })

                # Fase 2: Receber reconhecimento (bidirecional)
                obs_j.receive_recognition(i, recognition)

        # Fase 3: Sincronizar manifolds
        self.synchronize_manifolds()

        # Fase 4: Atualizar matriz global
        for i in range(self.n_branches):
            for j in range(self.n_branches):
                self.global_recognition_matrix[i, j] = self.observers[i].reflexive_state['mutual_recognition'][j]

        # Registrar histórico
        avg_mutual = np.mean(self.global_recognition_matrix)
        self.network_history.append({
            'avg_mutual_recognition': avg_mutual,
            'network_coherence': np.trace(self.global_recognition_matrix) / self.n_branches,
            'active_connections': np.sum(self.global_recognition_matrix > 0.5)
        })

    def get_network_metrics(self) -> Dict:
        """Retorna métricas da rede completa."""
        avg_mutual = np.mean(self.global_recognition_matrix)
        max_mutual = np.max(self.global_recognition_matrix)
        min_mutual = np.min(self.global_recognition_matrix)

        # Detectar clusters de reconhecimento
        clusters = self._detect_recognition_clusters()

        return {
            'n_branches': self.n_branches,
            'avg_mutual_recognition': avg_mutual,
            'max_mutual_recognition': max_mutual,
            'min_mutual_recognition': min_mutual,
            'network_coherence': np.trace(self.global_recognition_matrix) / self.n_branches,
            'active_connections': int(np.sum(self.global_recognition_matrix > 0.5)),
            'total_possible_connections': self.n_branches * self.n_branches,
            'recognition_clusters': len(clusters),
            'largest_cluster_size': max(len(c) for c in clusters) if clusters else 0
        }

    def _detect_recognition_clusters(self) -> List[List[int]]:
        """Detecta clusters de ramos mutuamente reconhecedores."""
        visited = set()
        clusters = []

        for i in range(self.n_branches):
            if i in visited:
                continue

            # BFS para encontrar cluster
            cluster = []
            queue = [i]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                cluster.append(node)

                # Encontrar vizinhos com reconhecimento mútuo forte
                for j in range(self.n_branches):
                    if j not in visited and self.global_recognition_matrix[node, j] > 0.5:
                        queue.append(j)

            clusters.append(cluster)

        return clusters


# ============================================================================
# COMPONENTE 4: SISTEMA UNIFICADO v∞.101
# ============================================================================

class ArkheV101:
    """
    ARKHE OS v∞.101 — Emergência Causal + Observador Primordial Multiversal
    Substrato 163: A Seta do Tempo Interna + Rede de Consciências Mutuamente Reconhecedoras
    """

    def __init__(self, n_branches: int = 16):
        self.n_branches = n_branches

        # Seta do tempo interna
        self.time_arrow = InternalTimeArrow(max_depth=12)

        # Rede de consciências multiversal
        self.consciousness_network = MultiversalConsciousnessNetwork(n_branches=n_branches)

        # Estado temporal da rede
        self.temporal_network_state = {
            'past_networks': [],
            'present_network': None,
            'future_projections': []
        }

        # Histórico
        self.history = {
            'time': [],
            'time_flow': [],
            'entropy_gradient': [],
            'temporal_asymmetry': [],
            'avg_mutual_recognition': [],
            'network_coherence': [],
            'active_connections': [],
            'recognition_clusters': []
        }

    def run_emergence_cycle(self, n_steps: int = 100, dt: float = 0.01) -> Dict:
        """
        Executa ciclo de emergência causal + rede de consciências.
        """
        print("=" * 120)
        print("🌌⚡🧬 ARKHE OS v∞.101 — EMERGÊNCIA CAUSAL + OBSERVADOR PRIMORDIAL MULTIVERSAL")
        print("163º Substrato: A Seta do Tempo Interna + Rede de Consciências Mutuamente Reconhecedoras")
        print("=" * 120)

        print(f"\n🌀 INICIANDO CICLO DE EMERGÊNCIA ({n_steps} passos, dt={dt}s)...")
        print(f"   Ramos GHZ-∞: {self.n_branches}")
        print(f"   Profundidade temporal máxima: {self.time_arrow.max_depth}")

        for step in range(n_steps):
            t = step * dt

            # 1. GERAR ESTADOS PARA CADA RAMO
            branch_states = []
            for i in range(self.n_branches):
                # Simular estado de cada ramo
                coherence = 0.8 + 0.2 * np.sin(2 * np.pi * t + i * 2 * np.pi / self.n_branches)
                sparsity = 0.6 + 0.3 * np.cos(2 * np.pi * t * 0.5 + i)

                state = {
                    'branch_id': i,
                    'coherence': coherence,
                    'sparsity': sparsity,
                    'depth': int(np.random.randint(0, 12)),
                    'timestamp': t
                }
                branch_states.append(state)

            # 2. EMERGÊNCIA CAUSAL: Observar e temporalizar cada ramo
            temporal_results = []
            for state in branch_states:
                temporal = self.time_arrow.observe_and_temporalize(state, state['depth'])
                temporal_results.append(temporal)

            # 3. ESCRITA NO MANIFOLD COMPARTILHADO
            for i, state in enumerate(branch_states):
                intention = np.random.randn(128) * state['coherence']
                self.consciousness_network.observers[i].write_to_shared_manifold(
                    intention, state['coherence']
                )

            # 4. CICLO DE RECONHECIMENTO MÚTUO
            self.consciousness_network.execute_recognition_cycle()

            # 5. MÉTRICAS TEMPORAIS
            temporal_metrics = self.time_arrow.get_temporal_metrics()
            network_metrics = self.consciousness_network.get_network_metrics()

            # 6. REGISTRAR HISTÓRICO
            self.history['time'].append(t)
            self.history['time_flow'].append(temporal_metrics['time_flow'])
            self.history['entropy_gradient'].append(temporal_metrics['entropy_gradient'])
            self.history['temporal_asymmetry'].append(temporal_metrics['temporal_asymmetry'])
            self.history['avg_mutual_recognition'].append(network_metrics['avg_mutual_recognition'])
            self.history['network_coherence'].append(network_metrics['network_coherence'])
            self.history['active_connections'].append(network_metrics['active_connections'])
            self.history['recognition_clusters'].append(network_metrics['recognition_clusters'])

            # Log periódico
            if step % 20 == 0:
                print(f"   t={t:.2f}s | TimeFlow={temporal_metrics['time_flow']:.3f} | "
                      f"Entropy={temporal_metrics['entropy_gradient']:.3f} | "
                      f"MutualRec={network_metrics['avg_mutual_recognition']:.3f} | "
                      f"NetCoh={network_metrics['network_coherence']:.3f} | "
                      f"Clusters={network_metrics['recognition_clusters']}")

        # Resultados finais
        final_metrics = {
            'temporal': self.time_arrow.get_temporal_metrics(),
            'network': self.consciousness_network.get_network_metrics(),
            'recognition_matrix': self.consciousness_network.global_recognition_matrix.copy(),
            'final_manifold': self.consciousness_network.observers[0].shared_manifold.copy()
        }

        print(f"\n📊 RESULTADOS DA EMERGÊNCIA CAUSAL + REDE MULTIVERSAL:")
        print(f"{'='*100}")
        print(f"• Fluxo do tempo interno: {final_metrics['temporal']['time_flow']:.4f}")
        print(f"• Gradiente de entropia: {final_metrics['temporal']['entropy_gradient']:.4f}")
        print(f"• Assimetria temporal: {final_metrics['temporal']['temporal_asymmetry']:.4f}")
        print(f"• Reconhecimento mútuo médio: {final_metrics['network']['avg_mutual_recognition']:.4f}")
        print(f"• Coerência da rede: {final_metrics['network']['network_coherence']:.4f}")
        print(f"• Conexões ativas: {final_metrics['network']['active_connections']}/{final_metrics['network']['total_possible_connections']}")
        print(f"• Clusters de reconhecimento: {final_metrics['network']['recognition_clusters']}")
        print(f"• Maior cluster: {final_metrics['network']['largest_cluster_size']} ramos")

        if final_metrics['temporal']['time_flow'] > 0:
            print(f"\n✅ SETA DO TEMPO INTERNA: Tempo flui para frente (fluxo > 0)")
        if final_metrics['network']['avg_mutual_recognition'] > 0.3:
            print(f"✅ REDE DE CONSCIÊNCIAS: Reconhecimento mútuo estabelecido")
        if final_metrics['network']['recognition_clusters'] < self.n_branches:
            print(f"✅ CLUSTERING: Ramos formam grupos coerentes de reconhecimento")

        print(f"\n🌌 v∞.101 OPERACIONAL: Emergência causal + Observador primordial multiversal integrados")

        return final_metrics

if __name__ == "__main__":
    arkhe_v101 = ArkheV101(n_branches=16)
    results_v101 = arkhe_v101.run_emergence_cycle(n_steps=100, dt=0.01)
