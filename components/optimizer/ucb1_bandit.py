import math

class CoherenceTensor7D:
    def __init__(self, phase, latency_us, power_mw, mercy_gap, security, privacy, interpretability):
        self.phase = phase
        self.latency_us = latency_us
        self.power_mw = power_mw
        self.mercy_gap = mercy_gap
        self.security = security
        self.privacy = privacy
        self.interpretability = interpretability

class KernelVariant:
    def __init__(self, id, target_latency, target_power):
        self.id = id
        self.target_latency = target_latency
        self.target_power = target_power
        self.pull_count = 1

    def meets_hard_limits(self, telemetry: CoherenceTensor7D):
        return telemetry.mercy_gap >= 0.04

class UCB1Bandit:
    """Seleciona variante ótima de kernel em tempo real."""

    def __init__(self, variants):
        self.variants = variants
        self.C = 1.0
        self.total_pulls = 1

    def select_variant(self, telemetry_7d: CoherenceTensor7D) -> int:
        # Máscara de segurança: exclui variantes que violam limites hard
        candidates = [v for v in self.variants if v.meets_hard_limits(telemetry_7d)]

        # Calcula UCB para cada candidato
        best_score = -float('inf')
        best_variant = None

        for variant in candidates:
            # Recompensa mercy-aware
            reward = self._compute_reward(variant, telemetry_7d)

            # Bônus de exploração
            exploration = self.C * math.sqrt(
                2.0 * math.log(self.total_pulls) / variant.pull_count
            )

            ucb = reward + exploration
            if ucb > best_score:
                best_score = ucb
                best_variant = variant

        return best_variant.id

    def _compute_reward(self, variant, telemetry: CoherenceTensor7D) -> float:
        # Recompensa composta: latência, potência, mercy gap
        lat_score = 1.0 - abs(telemetry.latency_us - variant.target_latency) / 100
        pow_score = 1.0 - abs(telemetry.power_mw - variant.target_power) / 50
        mercy_score = 1.0 - abs(telemetry.mercy_gap - 0.07) / 0.03

        # Penalidade harmônica: se uma dimensão falha, recompensa cai
        try:
            harmonic = 3.0 / (1/lat_score + 1/pow_score + 1/mercy_score)
        except ZeroDivisionError:
            harmonic = 0.0
        return harmonic
