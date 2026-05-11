from typing import Dict

class WisdomInvestor:
    def __init__(self, wisdom_oracle):
        self.omega = wisdom_oracle
    def decide(self, team_phi_c: float, polymath_scores: float, synergy_phi: float, risk_phi: float) -> bool:
        omega_I = (0.3 * team_phi_c + 0.3 * polymath_scores + 0.2 * synergy_phi - 0.2 * risk_phi)
        return omega_I >= self.omega.theta