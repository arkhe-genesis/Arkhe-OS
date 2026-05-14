# src/arkhe/mesh/phi_c_consensus.py
"""
Substrato 9006‑β — Φ_C Consensus Engine
Envia a mesma query para múltiplos LLMs e seleciona a resposta
que maximiza a coerência Φ_C, com governança e ancoragem temporal.
"""
import asyncio, hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from arkhe.mesh.multi_llm_orchestrator import MultiLLMMeshGateway, LLMNodeState
from arkhe.kernel.ping_governance_v2 import PingGovernanceKernelV2, GovernanceDecision, CounterArgument, FinalDecision
from arkhe.layers.constraints import TemporalChainClient

class ConsensusStrategy(Enum):
    MAX_PHI_C = "max_phi_c"               # Maior coerência individual
    WEIGHTED_AVERAGE = "weighted_avg"      # Média ponderada por Φ_C
    MAJORITY_VOTE = "majority_vote"        # Maioria simples
    GOVERNANCE_AUDITED = "governance"      # Passa pelo Spiral Ping

@dataclass
class ConsensusResult:
    """Resultado de consenso Φ_C entre múltiplos LLMs."""
    query: str
    query_hash: str
    responses: List[Dict]
    winner_node_id: str
    winner_response: str
    winner_phi_c: float
    consensus_strength: float  # 0‑1, quão forte é o consenso
    strategy: ConsensusStrategy
    total_nodes_queried: int
    nodes_responded: int
    elapsed_ms: float
    governance_seal: Optional[str] = None
    temporal_anchor: Optional[str] = None

class PhiCConsensusEngine:
    """
    Motor de consenso baseado em coerência Φ_C.

    Fluxo:
    1. Recebe query do usuário
    2. Envia simultaneamente para todos os nós LLM online
    3. Coleta respostas com métricas Φ_C
    4. Aplica estratégia de consenso
    5. Opcionalmente audita via Spiral Ping (governança)
    6. Ancorar resultado na TemporalChain
    7. Retorna resposta vencedora com prova de consenso
    """

    def __init__(self,
                 gateway: MultiLLMMeshGateway,
                 governance: PingGovernanceKernelV2,
                 temporal: TemporalChainClient,
                 min_respondents: int = 2):
        self.gateway = gateway
        self.governance = governance
        self.temporal = temporal
        self.min_respondents = min_respondents
        self.consensus_history: List[ConsensusResult] = []

    async def query_consensus(
        self,
        query: str,
        strategy: ConsensusStrategy = ConsensusStrategy.MAX_PHI_C,
        required_nodes: Optional[List[str]] = None,
        governance_audit: bool = False,
        context: Dict = None,
    ) -> ConsensusResult:
        """
        Executa query em múltiplos LLMs e retorna consenso Φ_C.

        Args:
            query: A pergunta a ser respondida
            strategy: Estratégia de seleção da resposta
            required_nodes: Lista opcional de nós a consultar (default: todos online)
            governance_audit: Se True, audita a resposta vencedora via Spiral Ping

        Returns:
            ConsensusResult com a resposta vencedora e métricas
        """
        query_hash = hashlib.sha3_256(query.encode()).hexdigest()[:16]

        # Selecionar nós para consulta
        if required_nodes:
            target_nodes = [n for n in required_nodes if n in self.gateway.nodes and self.gateway.nodes[n].is_online]
        else:
            target_nodes = self.gateway.get_online_nodes(min_phi_c=0.85)

        if len(target_nodes) < self.min_respondents:
            raise ValueError(f"Need at least {self.min_respondents} online nodes, have {len(target_nodes)}")

        # Enviar queries em paralelo
        start = time.time()
        tasks = [self.gateway.query_node(node_id, query, context) for node_id in target_nodes]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = (time.time() - start) * 1000

        # Filtrar respostas válidas
        valid_responses = [r for r in responses if isinstance(r, dict) and "error" not in r]

        if len(valid_responses) < self.min_respondents:
            raise ValueError(f"Only {len(valid_responses)} valid responses, need {self.min_respondents}")

        # Aplicar estratégia de consenso
        winner = self._apply_strategy(valid_responses, strategy)

        # Calcular força do consenso
        consensus_strength = self._compute_consensus_strength(valid_responses, winner)

        # Auditoria de governança se solicitada
        governance_seal = None
        if governance_audit:
            governance_seal = await self._audit_via_governance(query, winner, valid_responses)

        # Ancorar na TemporalChain
        temporal_anchor = self._anchor_consensus(query, winner, valid_responses, strategy)

        result = ConsensusResult(
            query=query,
            query_hash=query_hash,
            responses=valid_responses,
            winner_node_id=winner["node_id"],
            winner_response=winner["response"],
            winner_phi_c=winner["phi_c"],
            consensus_strength=consensus_strength,
            strategy=strategy,
            total_nodes_queried=len(target_nodes),
            nodes_responded=len(valid_responses),
            elapsed_ms=elapsed,
            governance_seal=governance_seal,
            temporal_anchor=temporal_anchor,
        )

        self.consensus_history.append(result)
        return result

    def _apply_strategy(self, responses: List[Dict], strategy: ConsensusStrategy) -> Dict:
        """Aplica a estratégia de consenso selecionada."""
        if strategy == ConsensusStrategy.MAX_PHI_C:
            # Selecionar resposta com maior Φ_C
            return max(responses, key=lambda r: r.get("phi_c", 0))

        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            # Combinar respostas ponderadas por Φ_C (para respostas textuais, retorna a de maior peso)
            weights = [r.get("phi_c", 0.5) for r in responses]
            total_weight = sum(weights)
            if total_weight == 0:
                return responses[0]
            # Para simplicidade, retorna a resposta com maior peso
            best_idx = weights.index(max(weights))
            return responses[best_idx]

        elif strategy == ConsensusStrategy.MAJORITY_VOTE:
            # Votação majoritária baseada em hash da resposta
            from collections import Counter
            response_hashes = [hashlib.sha3_256(r["response"].encode()).hexdigest()[:8] for r in responses]
            votes = Counter(response_hashes)
            winner_hash = votes.most_common(1)[0][0]
            for r in responses:
                if hashlib.sha3_256(r["response"].encode()).hexdigest()[:8] == winner_hash:
                    return r
            return responses[0]

        elif strategy == ConsensusStrategy.GOVERNANCE_AUDITED:
            # Primeiro seleciona por MAX_PHI_C, depois audita
            winner = max(responses, key=lambda r: r.get("phi_c", 0))
            return winner

        return responses[0]

    def _compute_consensus_strength(self, responses: List[Dict], winner: Dict) -> float:
        """
        Calcula a força do consenso (0‑1).

        Força = (Φ_C do vencedor / média dos demais) * (1 - variância dos Φ_C)
        """
        if len(responses) < 2:
            return 1.0

        phi_values = [r.get("phi_c", 0.5) for r in responses]
        winner_phi = winner.get("phi_c", 0.5)
        avg_others = (sum(phi_values) - winner_phi) / (len(phi_values) - 1) if len(phi_values) > 1 else winner_phi

        # Quanto maior a diferença do vencedor para os outros, mais forte o consenso
        dominance = winner_phi / max(avg_others, 0.01)

        # Quanto menor a variância, mais unânime
        variance = sum((p - winner_phi) ** 2 for p in phi_values) / len(phi_values)
        unanimity = 1.0 - min(variance * 10, 1.0)

        strength = (0.6 * min(dominance / 1.2, 1.0) + 0.4 * unanimity)
        return max(0.0, min(1.0, strength))

    async def _audit_via_governance(self, query: str, winner: Dict, all_responses: List[Dict]) -> str:
        """Audita a resposta vencedora via Spiral Ping."""
        audit_result = self.governance.audit_decision(
            decision_id=f"CONSENSUS-{hashlib.sha3_256(query.encode()).hexdigest()[:12]}",
            decision_description=f"Consensus response for: {query[:80]}",
            initial_confidence=winner.get("phi_c", 0.9),
            supporting_evidence=[
                f"Winner node: {winner['node_id']}",
                f"Winner Φ_C: {winner['phi_c']:.4f}",
                f"Total respondents: {len(all_responses)}",
            ],
            counter_evidence=[
                CounterArgument("Single node dominance risk", 0.3, "consensus", "oracle"),
                CounterArgument("Potential sycophancy in high Φ_C", 0.2, "bias", "mythos_gate"),
            ],
            risk_score=0.4,
            author_orcid="0009-0005-2697-4668",
            num_monte_carlo=50,
        )

        if audit_result.final_decision in [FinalDecision.REJECT, FinalDecision.ESCALATE]:
            print(f"⚠️  Governance rejected consensus winner: {audit_result.final_decision.name}")

        return audit_result.seal

    def _anchor_consensus(self, query: str, winner: Dict, all_responses: List[Dict], strategy: ConsensusStrategy) -> str:
        """Ancora o resultado do consenso na TemporalChain."""
        anchor_data = {
            "type": "llm_consensus",
            "query_hash": hashlib.sha3_256(query.encode()).hexdigest()[:16],
            "winner_node": winner["node_id"],
            "winner_phi_c": winner["phi_c"],
            "total_nodes": len(all_responses),
            "strategy": strategy.value,
            "timestamp": time.time(),
        }
        return self.temporal.anchor_content(
            content_hash=hashlib.sha3_256(json.dumps(anchor_data, sort_keys=True).encode()).hexdigest()[:16],
            metadata=anchor_data,
        )

    def get_consensus_stats(self) -> Dict:
        """Retorna estatísticas do motor de consenso."""
        if not self.consensus_history:
            return {"total": 0}

        return {
            "total_consensus_queries": len(self.consensus_history),
            "avg_consensus_strength": sum(c.consensus_strength for c in self.consensus_history) / len(self.consensus_history),
            "avg_nodes_responded": sum(c.nodes_responded for c in self.consensus_history) / len(self.consensus_history),
            "most_reliable_node": max(
                set(c.winner_node_id for c in self.consensus_history),
                key=lambda n: sum(1 for c in self.consensus_history if c.winner_node_id == n)
            ) if self.consensus_history else None,
        }
