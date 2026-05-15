import asyncio
from datetime import datetime
from typing import Dict, List
import numpy as np

class EvolutionaryLoop:
    """
    Substrato 180‑C: Aprendizado federado contínuo com ajuste dinâmico de pesos.
    """
    def __init__(self, consensus_engine, phi_bus, temporal, privacy_engine):
        self.consensus = consensus_engine
        self.phi_bus = phi_bus
        self.temporal = temporal
        self.privacy = privacy_engine  # 180‑D

    async def run(self, interval_minutes=15):
        while True:
            try:
                # 1. Coletar métricas de coerência recentes por nó
                node_metrics = await self.phi_bus.get_coherence_window(minutes=60)

                # 2. Detectar padrões de degradação ou oportunidade de melhoria
                adjustments = self._compute_weight_adjustments(node_metrics)

                # 3. Preparar atualização de modelo federado (apenas gradientes)
                global_update = await self._federated_aggregation(node_metrics)

                # 4. Aplicar privacidade diferencial (epsilon, delta) ao update
                safe_update = self.privacy.apply_dp(global_update, epsilon=0.5, delta=1e-5)

                # 5. Submeter ao MAC Consensus para validação do novo modelo
                approved = await self.consensus.propose_model_update(
                    update=safe_update,
                    min_phi_c=0.999
                )

                if approved:
                    # 6. Distribuir o modelo atualizado a todos os nós (broadcast cego)
                    await self._broadcast_model_update(safe_update)

                    # 7. Ajustar pesos dos nós com base no desempenho relativo
                    await self.consensus.adjust_weights(adjustments)

                    # 8. Ancorar o evento na TemporalChain
                    await self.temporal.anchor_event(
                        event_type="evolutionary_cycle",
                        payload={
                            "timestamp": datetime.utcnow().isoformat(),
                            "nodes_participating": len(node_metrics),
                            "privacy_epsilon": 0.5,
                            "model_version": safe_update["version"]
                        }
                    )

            except Exception as e:
                # Registrar falha, não interromper o loop
                if self.temporal:
                    await self.temporal.anchor_event("evolution_error", {"error": str(e)})

            await asyncio.sleep(interval_minutes * 60)

    def _compute_weight_adjustments(self, metrics: Dict) -> Dict[str, float]:
        """
        Penaliza nós com menor coerência ou latência excessiva.
        Recompensa consistência.
        """
        adjustments = {}
        for node_id, stats in metrics.items():
            avg_phi = stats['avg_phi_c']
            if avg_phi < 0.98:
                adjustments[node_id] = -0.01  # penalidade
            elif avg_phi > 0.999:
                adjustments[node_id] = 0.005  # recompensa
        return adjustments

    async def _federated_aggregation(self, metrics: Dict) -> Dict:
        """
        Simula agregação federada real: cada nó treina localmente e envia
        gradientes (não dados). Aqui, por simplicidade, calculamos uma média
        ponderada dos 'pesos de contribuição' que seriam substituídos por
        um protocolo como FedAvg com Secure Aggregation.
        """
        total_weight = sum(m['weight'] for m in metrics.values())
        aggregated_update = {
            "version": int(datetime.utcnow().timestamp()),
            "gradients": np.mean([m['local_gradients'] for m in metrics.values()], axis=0).tolist()
        }
        return aggregated_update

    async def _broadcast_model_update(self, update: Dict):
        # Enviar modelo para todos os nós via canal criptografado
        await self.phi_bus.broadcast("global_model_update", update)
