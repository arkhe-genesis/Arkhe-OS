"""
royalty_ledger_extended.py — Ledger estendido para distribuição de royalties.
Integra contrato .casi com ledger de auditoria e DHT.
"""
import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class RoyaltyTransaction:
    """Transação de royalty para auditoria."""
    tx_id: str
    viewer_seal: str
    creator_id: str
    stream_id: str
    amount: float
    coherence_contribution: float
    kym_weight: float
    timestamp: float
    cas_contract_hash: str
    ledger_signature: str

class RoyaltyLedgerExtended:
    """Ledger estendido para distribuição automática de royalties."""

    def __init__(self, cas_runtime, audit_ledger, dht_client):
        self.cas = cas_runtime  # Runtime para executar contratos .casi
        self.audit = audit_ledger  # Ledger de auditoria (Substrato 333)
        self.dht = dht_client  # DHT para descoberta (Substrato 330)

        self.pending_distributions: List[RoyaltyTransaction] = []
        self.distribution_interval = 3600  # Distribuir a cada hora

    async def record_view_completion(self,
                                    viewer_seal: str,
                                    stream_id: str,
                                    watch_duration: int,
                                    kym_proof: Dict) -> Dict:
        """Registra conclusão de visualização e calcula royalties."""

        # Executar contrato .casi para calcular royalty
        contract_result = await self.cas.execute_contract(
            contract_name="RoyaltyDistributionEngine",
            function="end_viewing_session",
            params={
                "viewer_seal": viewer_seal,
                "stream_id": stream_id,
                "watch_duration": watch_duration,
                "kym_proof": kym_proof
            }
        )

        if not contract_result.get("success"):
            return {"error": contract_result.get("error")}

        # Criar transação para auditoria
        tx = RoyaltyTransaction(
            tx_id=hashlib.sha256(
                f"{viewer_seal}:{stream_id}:{time.time()}".encode()
            ).hexdigest()[:16],
            viewer_seal=viewer_seal,
            creator_id=contract_result["creator_id"],
            stream_id=stream_id,
            amount=contract_result["royalty"],
            coherence_contribution=contract_result["coherence_contribution"],
            kym_weight=contract_result["viewer_weight"],
            timestamp=time.time(),
            cas_contract_hash=contract_result["contract_hash"],
            ledger_signature=self._sign_transaction(contract_result)
        )

        # Publicar no ledger de auditoria
        await self.audit.record_transaction(
            tx_type="royalty_distribution",
            data=asdict(tx),
            signature=tx.ledger_signature
        )

        # Adicionar à fila de distribuição em lote
        self.pending_distributions.append(tx)

        return {
            "success": True,
            "tx_id": tx.tx_id,
            "royalty_amount": tx.amount,
            "coherence_bonus": tx.coherence_contribution
        }

    async def batch_distribute_royalties(self):
        """Distribui royalties em lote para otimização de custos."""
        if not self.pending_distributions:
            return {"status": "no_pending"}

        # Agrupar por criador
        by_creator: Dict[str, List[RoyaltyTransaction]] = {}
        for tx in self.pending_distributions:
            if tx.creator_id not in by_creator:
                by_creator[tx.creator_id] = []
            by_creator[tx.creator_id].append(tx)

        # Executar distribuição via contrato .casi
        distribution_results = []
        for creator_id, txs in by_creator.items():
            total_amount = sum(tx.amount for tx in txs)

            result = await self.cas.execute_contract(
                contract_name="RoyaltyDistributionEngine",
                function="distribute_to_creator",
                params={
                    "creator_id": creator_id,
                    "total_amount": total_amount,
                    "transaction_ids": [tx.tx_id for tx in txs]
                }
            )

            distribution_results.append({
                "creator_id": creator_id,
                "total_distributed": total_amount,
                "tx_count": len(txs),
                "contract_result": result
            })

            # Limpar transações distribuídas
            self.pending_distributions = [
                tx for tx in self.pending_distributions
                if tx.creator_id != creator_id
            ]

        return {
            "status": "distributed",
            "creators_paid": len(distribution_results),
            "results": distribution_results
        }

    def _sign_transaction(self, data: Dict) -> str:
        """Assina transação para integridade do ledger."""
        # Em produção: assinatura Ed25519 com chave do ledger
        payload = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()[:64]

    async def query_creator_earnings(self,
                                    creator_id: str,
                                    time_range: Optional[tuple] = None) -> Dict:
        """Consulta ganhos de um criador no período especificado."""
        # Consultar ledger de auditoria
        query = {
            "tx_type": "royalty_distribution",
            "filters": {"creator_id": creator_id}
        }
        if time_range:
            query["time_range"] = {"start": time_range[0], "end": time_range[1]}

        transactions = await self.audit.query_transactions(query)

        # Calcular totais
        total_earned = sum(tx["amount"] for tx in transactions)
        avg_coherence = sum(tx["coherence_contribution"] for tx in transactions) / max(1, len(transactions))

        return {
            "creator_id": creator_id,
            "total_earned": total_earned,
            "transaction_count": len(transactions),
            "avg_coherence_contribution": avg_coherence,
            "time_range": time_range or "all_time",
            "transactions": transactions[:100]  # Últimas 100 transações
        }