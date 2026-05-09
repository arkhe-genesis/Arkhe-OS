"""
channel_score.py — Motor de reputação Φ-REP para canais IPTV.
Integra com Substrato 344 e KYM para ponderar votos.
"""
import numpy as np
from typing import Dict, List

class ChannelReputationEngine:
    def __init__(self, alpha: float = 0.85):
        self.alpha = alpha
        self.channel_scores: Dict[str, float] = {}

    def update_reputation(self, channel_id: str, votes: List[Dict], current_phi: float) -> float:
        """Atualiza Φ-REP do canal com base em votos ponderados por KYM."""
        valid_votes = [v for v in votes if v.get("kym_verified")]
        if not valid_votes:
            return self.channel_scores.get(channel_id, 0.5)

        weights = [self.alpha * v["voter_phi_rep"] for v in valid_votes]
        values = [v["rating"] for v in valid_votes]

        new_rep = np.average(values, weights=weights)
        prev = self.channel_scores.get(channel_id, 0.5)
        self.channel_scores[channel_id] = 0.7 * prev + 0.3 * new_rep
        return self.channel_scores[channel_id]
