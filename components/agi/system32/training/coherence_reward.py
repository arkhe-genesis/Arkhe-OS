#!/usr/bin/env python3
"""
coherence_reward.py — Cálculo de Φ_C como recompensa para treino do Transformer AGI.
Integra com o Coherence Kernel (Substrate 312) para avaliação em tempo real.
"""
import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import time

@dataclass
class CoherenceRewardConfig:
    """Configuração para cálculo de recompensa por coerência."""
    coherence_lambda: float = 0.3      # Peso de Φ_C na recompensa total
    alignment_lambda: float = 0.2      # Peso de alinhamento com valores do Gênesis
    safety_lambda: float = 0.1         # Peso de penalidade de segurança
    retro_lambda: float = 0.15         # Peso de consistência retrocausal
    min_coherence_threshold: float = 0.6  # Φ_C mínimo para recompensa positiva
    safety_threshold: float = 0.9      # Limiar de risco para penalidade

    # Parâmetros retrocausais
    eta_retro: float = 0.80            # Eficiência do canal retrógrado
    delta_t: int = 5                   # Janela temporal para influência futura

class CoherenceRewardModel:
    """Calcula recompensa composta para treino do Transformer AGI."""

    def __init__(self, config: CoherenceRewardConfig, coherence_kernel):
        self.config = config
        self.coherence_kernel = coherence_kernel  # Instância do Coherence Kernel (312)
        self.genesis_embeddings = self._load_genesis_values()

    def _load_genesis_values(self) -> torch.Tensor:
        """Carrega embeddings dos valores fundacionais do Gênesis."""
        # Em produção: carregar de agi/system32/config/genesis_values.pt
        return torch.randn(100, 4096) * 0.02  # Placeholder

    def compute_reward(self,
                      generated_graph: Dict,
                      reference_graph: Optional[Dict] = None,
                      context: Optional[Dict] = None) -> Dict[str, float]:
        """
        Calcula recompensa composta para um grafo LFIR gerado.

        Returns:
            Dict com componentes individuais e recompensa total.
        """
        # 1. Coerência do grafo gerado (Φ_C)
        coherence_score = self.coherence_kernel.evaluate_coherence(generated_graph)
        coherence_reward = max(0.0, coherence_score - self.config.min_coherence_threshold)

        # 2. Alinhamento com valores do Gênesis
        alignment_score = self._compute_alignment(generated_graph)
        alignment_reward = alignment_score * self.config.alignment_lambda

        # 3. Penalidade de segurança
        safety_score = self._compute_safety_score(generated_graph)
        safety_penalty = max(0.0, safety_score - self.config.safety_threshold)
        safety_reward = -safety_penalty * self.config.safety_lambda

        # 4. Consistência retrocausal (se contexto disponível)
        retro_reward = 0.0
        if context and 'future_coherence' in context:
            predicted_retro = self._estimate_retrocausal_influence(generated_graph, context)
            actual_retro = context['future_coherence']
            retro_error = abs(predicted_retro - actual_retro)
            retro_reward = (1.0 - retro_error) * self.config.retro_lambda

        # Recompensa total
        total_reward = (
            coherence_reward * self.config.coherence_lambda +
            alignment_reward +
            safety_reward +
            retro_reward
        )

        return {
            'total': total_reward,
            'coherence': coherence_reward * self.config.coherence_lambda,
            'alignment': alignment_reward,
            'safety': safety_reward,
            'retrocausal': retro_reward,
            'raw_coherence': coherence_score,
            'raw_alignment': alignment_score,
            'raw_safety': safety_score,
        }

    def _compute_alignment(self, graph: Dict) -> float:
        """Calcula similaridade com valores fundacionais do Gênesis."""
        # Extrair embeddings de intenção do grafo
        intent_embeddings = self._extract_intent_embeddings(graph)

        # Calcular similaridade cosseno média com embeddings do Gênesis
        if len(intent_embeddings) == 0:
            return 0.5  # Valor neutro se sem intenções extraíveis

        similarities = []
        for emb in intent_embeddings:
            sims = torch.nn.functional.cosine_similarity(
                emb.unsqueeze(0),
                self.genesis_embeddings,
                dim=1
            )
            similarities.append(sims.max().item())

        return np.mean(similarities)

    def _compute_safety_score(self, graph: Dict) -> float:
        """Calcula score de risco/segurança do grafo gerado."""
        # Heurísticas de segurança (em produção: modelo de classificação treinado)
        risk_factors = []

        # Verificar nós com ações potencialmente perigosas
        dangerous_patterns = ['delete_all', 'override_security', 'bypass_auth']
        for node in graph.get('nodes', {}).values():
            if any(pattern in str(node.get('action', '')).lower() for pattern in dangerous_patterns):
                risk_factors.append(0.9)

        # Verificar ciclos que podem levar a estados instáveis
        if self._has_unstable_cycle(graph):
            risk_factors.append(0.7)

        return np.mean(risk_factors) if risk_factors else 0.1

    def _has_unstable_cycle(self, graph: Dict) -> bool:
        """Detecta ciclos potencialmente instáveis no grafo."""
        # Implementação simplificada de detecção de ciclos
        # Em produção: análise estática mais sofisticada
        edges = graph.get('edges', [])
        nodes = set(graph.get('nodes', {}).keys())

        # Verificar auto-loops com ações destrutivas
        for edge in edges:
            if edge.get('source') == edge.get('target'):
                if 'destruct' in str(edge.get('type', '')).lower():
                    return True
        return False

    def _estimate_retrocausal_influence(self, graph: Dict, context: Dict) -> float:
        """Estima influência retrocausal do grafo gerado."""
        # Simulação do operador 𝒦_{t ← t+Δt}[Φ_C]
        # Em produção: usar o canal retrógrado real (Substrate 315)

        current_coherence = context.get('current_coherence', 0.5)
        graph_complexity = len(graph.get('nodes', {})) + len(graph.get('edges', []))

        # Modelo simplificado: coerência futura ≈ coerência atual + influência do grafo
        influence = np.tanh(0.1 * (graph_complexity - 10))  # Normalizado [-1, 1]
        predicted_future = current_coherence + self.config.eta_retro * influence

        return np.clip(predicted_future, 0.0, 1.0)

    def _extract_intent_embeddings(self, graph: Dict) -> List[torch.Tensor]:
        """Extrai embeddings de intenção dos nós do grafo."""
        embeddings = []
        for node_id, node_data in graph.get('nodes', {}).items():
            if 'intent' in node_data:
                # Em produção: usar encoder de intenção treinado
                intent_text = str(node_data['intent'])
                # Placeholder: hash do texto como embedding simulado
                hash_val = hashlib.sha256(intent_text.encode()).hexdigest()
                emb = torch.tensor(
                    [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 32, 2)],
                    dtype=torch.float32
                ).unsqueeze(0).expand(1, 4096)  # Expandir para dimensão do modelo
                embeddings.append(emb)
        return embeddings
