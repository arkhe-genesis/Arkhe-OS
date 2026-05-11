"""
kym_gatekeeper.py — Verificação de identidade para espectadores e criadores.
Integra com Substrato 5006 (KYM) e bloqueia bots/sybil.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class KYMProfile:
    seal: str
    phi_risk: float
    is_human: bool
    last_verified: float

class KYMGatekeeper:
    """Controla acesso ao streaming com base em KYM."""
    def __init__(self, kym_verifier, risk_threshold: float = 0.5):
        self.kym = kym_verifier
        self.risk_threshold = risk_threshold
        self.banned_seals = set()

    def verify_and_grant_access(self, node_seal: str, challenge: str = "") -> bool:
        profile = self.kym.run_kym(node_seal, challenge)
        if profile.phi_risk > self.risk_threshold or not profile.is_human:
            self.banned_seals.add(node_seal)
            return False
        return True

    def get_viewer_weight(self, node_seal: str) -> float:
        """Peso do viewer para cálculos de royalties."""
        profile = self.kym.run_kym(node_seal)
        return max(0.1, 1.0 - profile.phi_risk)
