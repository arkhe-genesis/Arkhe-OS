import numpy as np
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

from arkhe_os.network.rcp_message import RetroPhase

class SecurityError(Exception):
    pass

class ConsensusPhase(Enum):
    """Fases do protocolo de consenso temporal."""
    PROPOSAL = "proposal"        # Nós propõem medições e post-selections
    MEASUREMENT = "measurement"  # Executam weak measurements locais
    AGGREGATION = "aggregation"  # Agregam resultados via RCP
    VALIDATION = "validation"    # Validam violação de Leggett-Garg global
    COMMIT = "commit"           # Comprometem-se com estado coerente

@dataclass
class TemporalMeasurement:
    """Medição temporal para teste de Leggett-Garg."""
    node_id: str
    timestamp: float
    observable: str
    value: float
    weak_uncertainty: float
    phase: RetroPhase  # Do RetrocausalGradientEngine
    signature: bytes   # Assinatura quântica para autenticidade

@dataclass
class LeggettGargProposal:
    """Proposta de teste de Leggett-Garg para consenso."""
    proposal_id: str
    proposer_node: str
    observable: str
    time_points: List[float]  # [t1, t2, t3] para C21, C32, C31
    target_K: float  # Valor alvo de K (deve ser > 1 para quântico)
    confidence_threshold: float  # σ mínimo para validação
    expiration: float  # Timestamp de expiração da proposta

class FederatedTemporalConsensus:
    """
    Orquestra consenso temporal distribuído via violação de Leggett-Garg.

    Fluxo do protocolo:
    1. PROPOSAL: Um nó propõe um teste LG com observável e tempos específicos
    2. MEASUREMENT: Nós participantes executam weak measurements nos tempos especificados
    3. AGGREGATION: Resultados são agregados via canais RCP (com autenticação QKD)
    4. VALIDATION: Calcula-se K_global e verifica-se violação com confiança estatística
    5. COMMIT: Se validado, nós atualizam seus estados locais com gradientes retrocausais agregados
    """

    def __init__(self, node_id: str, rcp_interface: any,
                 min_participants: int = 3, significance_threshold: float = 3.0):
        self.node_id = node_id
        self.rcp_interface = rcp_interface
        self.min_participants = min_participants
        self.significance_threshold = significance_threshold
        self.pending_proposals: Dict[str, LeggettGargProposal] = {}
        self.collected_measurements: Dict[str, List[TemporalMeasurement]] = {}

    def propose_temporal_test(
        self,
        observable: str,
        time_points: List[float],
        target_K: float = 1.2,
        confidence: float = 3.0
    ) -> str:
        """Propõe um novo teste de Leggett-Garg para a rede."""
        proposal = LeggettGargProposal(
            proposal_id=f"lg_{self.node_id}_{np.random.randint(10000)}",
            proposer_node=self.node_id,
            observable=observable,
            time_points=time_points,
            target_K=target_K,
            confidence_threshold=confidence,
            expiration=time.time() + 300  # 5 minutos de validade
        )

        # Broadcast proposal via canal clássico (para descoberta)
        self.rcp_interface.broadcast_classical("LG_PROPOSAL", proposal)
        self.pending_proposals[proposal.proposal_id] = proposal

        return proposal.proposal_id

    def submit_measurement(self, proposal_id: str, measurement: TemporalMeasurement):
        """Submete uma medição temporal para um teste em andamento."""
        if proposal_id not in self.pending_proposals:
            raise ValueError(f"Proposal {proposal_id} not found or expired")

        # Verificar assinatura quântica (autenticidade)
        if not self._verify_quantum_signature(measurement):
            raise SecurityError("Invalid quantum signature on measurement")

        # Armazenar medição localmente
        if proposal_id not in self.collected_measurements:
            self.collected_measurements[proposal_id] = []
        self.collected_measurements[proposal_id].append(measurement)

        # Encaminhar via canal RCP para agregação retrocausal
        self.rcp_interface.send_retrocausal(
            target_nodes="all_participants",
            payload={"type": "LG_MEASUREMENT", "proposal_id": proposal_id, "measurement": measurement},
            phase=RetroPhase.PHI_0  # Fluxo futuro→passado para aceleração de consenso
        )

    def evaluate_consensus(self, proposal_id: str) -> Dict[str, any]:
        """Avalia se consenso temporal foi alcançado para um teste."""
        if proposal_id not in self.pending_proposals:
            return {"error": "Proposal not found"}

        measurements = self.collected_measurements.get(proposal_id, [])

        # Verificar número mínimo de participantes
        participating_nodes = set(m.node_id for m in measurements)
        if len(participating_nodes) < self.min_participants:
            return {
                "status": "insufficient_participants",
                "current": len(participating_nodes),
                "required": self.min_participants
            }

        # Agrupar medições por nó e calcular correlações locais
        node_correlations = {}
        for node in participating_nodes:
            node_measurements = [m for m in measurements if m.node_id == node]
            if len(node_measurements) >= 3:
                # Calcular C21, C32, C31 para este nó
                sorted_meas = sorted(node_measurements, key=lambda m: m.timestamp)
                v1, v2, v3 = sorted_meas[0].value, sorted_meas[1].value, sorted_meas[2].value
                C21 = v2 * v1
                C32 = v3 * v2
                C31 = v3 * v1
                node_correlations[node] = {"K": C21 + C32 - C31, "uncertainty": self._estimate_node_uncertainty(node_measurements)}

        if not node_correlations:
            return {"status": "insufficient_data_per_node"}

        # Calcular K_global como média ponderada pelas incertezas
        weights = {node: 1.0/(corr["uncertainty"]**2 + 1e-6) for node, corr in node_correlations.items()}
        total_weight = sum(weights.values())
        K_global = sum(weights[node] * node_correlations[node]["K"] for node in node_correlations) / total_weight
        sigma_global = np.sqrt(1.0 / total_weight)

        # Verificar violação de Leggett-Garg
        threshold = 1.0 + self.significance_threshold * sigma_global
        violation = K_global > threshold
        significance = (K_global - 1.0) / sigma_global if sigma_global > 0 else 0

        result = {
            "status": "validated" if violation else "not_validated",
            "K_global": K_global,
            "sigma_global": sigma_global,
            "threshold": threshold,
            "violation": violation,
            "significance": significance,
            "participating_nodes": list(participating_nodes),
            "node_correlations": node_correlations
        }

        # Se validado, broadcast commit para atualização de estados
        if violation:
            self.rcp_interface.broadcast_retrocausal(
                payload={"type": "LG_COMMIT", "proposal_id": proposal_id, "K_global": K_global},
                phase=RetroPhase.PHI_0
            )

        return result

    def _verify_quantum_signature(self, measurement: TemporalMeasurement) -> bool:
        """Verifica assinatura quântica via QKD (simulado aqui)."""
        # Em produção: usar protocolo E91 ou BB84 para verificação
        # Aqui: simulação baseada em nonce compartilhado
        expected_nonce = self.rcp_interface.get_shared_nonce(measurement.node_id)
        return measurement.signature == self._compute_signature(measurement, expected_nonce)

    def _estimate_node_uncertainty(self, measurements: List[TemporalMeasurement]) -> float:
        """Estima incerteza agregada para medições de um nó."""
        if len(measurements) < 3:
            return 1.0  # Alta incerteza para poucas amostras
        values = [m.value for m in measurements]
        return np.std(values) / np.sqrt(len(values))  # Erro padrão da média

    def _compute_signature(self, measurement: TemporalMeasurement, nonce: bytes) -> bytes:
        """Computa assinatura simulada para autenticação."""
        import hashlib
        data = f"{measurement.node_id}{measurement.timestamp}{measurement.observable}{measurement.value}{nonce.hex()}".encode()
        return hashlib.sha3_256(data).digest()[:16]  # 128-bit signature
