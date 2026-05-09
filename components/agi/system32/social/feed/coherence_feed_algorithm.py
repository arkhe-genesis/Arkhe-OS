#!/usr/bin/env python3
"""
coherence_feed_algorithm.py — Algoritmo de feed que prioriza coerência, não engajamento.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time

@dataclass
class SocialPost:
    """Post em uma rede social soberana."""
    post_id: str
    author_seal: str
    content: str                    # Texto ou hash de conteúdo multimídia
    content_type: str              # "text", "image", "video", "lfir_intention"
    signature: str                  # Assinatura criptográfica do autor
    timestamp: float
    coherence_score: float         # Φ_C do conteúdo (calculado no post)
    parent_post_id: Optional[str] = None  # Para threads/respostas
    meta: Dict = field(default_factory=dict)

    # Métricas sociais (derivadas, não armazenadas no post)
    reply_count: int = 0
    coherence_weighted_score: float = 0.0  # Calculado pelo algoritmo

class CoherenceFeedAlgorithm:
    """
    Algoritmo de curadoria de feed baseado em coerência.

    Fórmula de ranking:
    score(post) = w1·Φ_C(post) + w2·Φ_REP(author) + w3·network_coherence + w4·temporal_decay
    """

    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 temporal_decay_hours: float = 24.0):
        # Pesos canônicos (configuráveis)
        self.weights = weights or {
            "content_coherence": 0.40,   # Φ_C do próprio post
            "author_reputation": 0.30,    # Φ-REP do autor
            "network_coherence": 0.20,    # Coerência média dos que interagiram
            "temporal_freshness": 0.10    # Decaimento temporal
        }
        self.temporal_decay_hours = temporal_decay_hours

    def calculate_post_score(self,
                            post: SocialPost,
                            author_phi_rep: float,
                            network_coherence: float,
                            current_time: float) -> float:
        """Calcula score de ranking para um post."""
        # 1. Coerência do conteúdo
        content_coh = post.coherence_score

        # 2. Reputação do autor
        author_rep = author_phi_rep

        # 3. Coerência da rede (média de Φ_C dos que curtiram/comentaram)
        net_coh = network_coherence

        # 4. Decaimento temporal (posts recentes têm bónus)
        hours_old = (current_time - post.timestamp) / 3600
        temporal_factor = np.exp(-hours_old / self.temporal_decay_hours)

        # Score combinado
        score = (
            self.weights["content_coherence"] * content_coh +
            self.weights["author_reputation"] * author_rep +
            self.weights["network_coherence"] * net_coh +
            self.weights["temporal_freshness"] * temporal_factor
        )

        return float(min(1.0, max(0.0, score)))  # Clamp [0, 1]

    def rank_posts(self,
                   posts: List[SocialPost],
                   user_seal: str,
                   profile_manager,
                   current_time: Optional[float] = None) -> List[SocialPost]:
        """
        Ranqueia posts para o feed de um usuário.

        Considera:
        - Coerência do conteúdo
        - Reputação do autor
        - Conexões do usuário (follows)
        - Histórico de interações
        """
        if current_time is None:
            current_time = time.time()

        scored_posts = []

        for post in posts:
            # Obter reputação do autor
            author_profile = profile_manager.get_profile(post.author_seal)
            author_phi_rep = author_profile.phi_rep if author_profile else 0.5

            # Calcular coerência da rede (simplificado: média dos followers do usuário)
            # Em produção: calcular baseado em interações reais
            network_coh = 0.75  # Placeholder

            # Calcular score
            score = self.calculate_post_score(
                post, author_phi_rep, network_coh, current_time
            )
            post.coherence_weighted_score = score
            scored_posts.append(post)

        # Ordenar por score descendente
        scored_posts.sort(key=lambda p: p.coherence_weighted_score, reverse=True)

        return scored_posts

    def filter_low_coherence(self,
                           posts: List[SocialPost],
                           threshold: float = 0.6) -> List[SocialPost]:
        """Filtra posts com coerência abaixo do threshold."""
        return [p for p in posts if p.coherence_score >= threshold]

    def detect_manipulation_attempt(self,
                                   posts: List[SocialPost],
                                   time_window_seconds: float = 300) -> List[Dict]:
        """
        Detecta padrões suspeitos: muitos posts de baixa coerência em curto período.
        """
        alerts = []
        # Agrupar posts por autor
        by_author: Dict[str, List[SocialPost]] = {}
        for post in posts:
            if post.author_seal not in by_author:
                by_author[post.author_seal] = []
            by_author[post.author_seal].append(post)

        # Analisar cada autor
        for author, author_posts in by_author.items():
            # Posts recentes
            recent = [p for p in author_posts
                     if time.time() - p.timestamp < time_window_seconds]

            if len(recent) > 10:  # Threshold de volume
                avg_coh = np.mean([p.coherence_score for p in recent])
                if avg_coh < 0.5:  # Baixa coerência média
                    alerts.append({
                        "author_seal": author,
                        "pattern": "high_volume_low_coherence",
                        "post_count": len(recent),
                        "avg_coherence": avg_coh,
                        "time_window": time_window_seconds
                    })

        return alerts
