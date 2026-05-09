import asyncio
from typing import Any

from arkhe_os.coherence.path_coherence_estimator import AdaptiveBaselineEstimator
from arkhe_os.parser.frontends.ping_frontend_async import PingResult

# Note: We assume the target interface of MRCController provides these coroutines
class MRCControllerStub:
    async def update_path_coherence(self, destination: str, coherence_score: float, metrics: dict):
        pass

    async def trigger_active_probe(self, target: str, reason: str):
        pass

class PingToMRCProbeAdapter:
    """Converte métricas de ping em probes estruturados para o MRC."""

    def __init__(self, mrc_controller: Any, coherence_estimator: AdaptiveBaselineEstimator, trigger_threshold: float = 0.6):
        self.mrc = mrc_controller
        self.estimator = coherence_estimator
        self.trigger_threshold = trigger_threshold

    async def sync_path_health(self, target: str, ping_result: PingResult):
        """Alimenta o MRC com saúde de caminho calculada a partir de ping."""

        # Ensure baseline is updated before calculating coherence
        self.estimator.update_baseline(target, ping_result.rtt_avg_ms)

        coherence = self.estimator.compute_coherence(
            target, ping_result.rtt_avg_ms, ping_result.loss_rate, ping_result.jitter_ms
        )

        # update the PingResult with calculated coherence for auditing purposes
        ping_result.coherence = coherence

        # Atualiza estado do caminho no MRC
        await self.mrc.update_path_coherence(
            destination=target,
            coherence_score=coherence,
            metrics={
                "rtt_avg": ping_result.rtt_avg_ms,
                "loss": ping_result.loss_rate,
                "jitter": ping_result.jitter_ms,
                "ttl": ping_result.ttl
            }
        )

        # Se coerência cair abaixo de threshold, dispara probe ativo
        if coherence < self.trigger_threshold:
            await self.mrc.trigger_active_probe(target, reason="low_coherence")
