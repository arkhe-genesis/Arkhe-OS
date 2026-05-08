import numpy as np
import time
import asyncio
import hashlib
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from collections import defaultdict

from arkhe_os.network.rcp_message import RCPMessage, RCPMessageType, RetroPhase

@dataclass
class WeakValueGradient:
    observable: str
    real_part: float
    imag_part: float
    uncertainty: float
    phase: RetroPhase
    timestamp: float

@dataclass
class AlignmentSnapshot:
    """Snapshot do estado de alinhamento de um nó em um momento."""
    node_id: str
    timestamp: float
    value_vector: Dict[str, float]  # Mapeamento valor → peso/importância
    coherence_score: float
    safety_metrics: Dict[str, float]  # Métricas de segurança locais
    temporal_proof: str  # Hash da prova de coerência temporal

@dataclass
class AlignmentDriftAlert:
    """Alerta de drift de alinhamento detectado distribuídamente."""
    alert_id: str
    detected_by: str  # Nó que detectou o drift
    affected_node: str  # Nó com drift potencial
    drift_magnitude: float  # Quão significativo é o drift
    affected_values: List[str]  # Quais valores estão desalinhados
    retrocausal_evidence: List[WeakValueGradient]  # Evidência via weak values
    recommended_action: str  # Sugestão de intervenção
    confidence: float  # Confiança na detecção (0-1)

class DistributedAlignmentMonitor:
    """
    Monitora alinhamento de valores através da rede federada usando inferência retrocausal.

    Mecanismo:
    1. Cada nó periodicamente publica AlignmentSnapshot via RCP
    2. Nós vizinhos comparam snapshots via gradientes retrocausais para detectar drift
    3. Se drift detectado com alta confiança, emite AlignmentDriftAlert
    4. Alerta dispara intervenção coordenada (fallback, human-in-loop, etc.)
    """

    def __init__(self, node_id: str, rcp_interface: any,
                 drift_threshold: float = 0.15, confidence_threshold: float = 0.8):
        self.node_id = node_id
        self.rcp_interface = rcp_interface
        self.drift_threshold = drift_threshold  # Limite para considerar drift significativo
        self.confidence_threshold = confidence_threshold  # Confiança mínima para alertar
        self.local_snapshots: List[AlignmentSnapshot] = []  # Histórico local
        self.remote_snapshots: Dict[str, List[AlignmentSnapshot]] = defaultdict(list)  # Por nó remoto
        self.alert_callbacks: List[Callable[[AlignmentDriftAlert], Awaitable[None]]] = []

        # Registrar handler para receber snapshots de outros nós
        rcp_interface.register_handler(RCPMessageType.COHERENCE_PROOF, self._handle_remote_snapshot)

    def publish_local_snapshot(self, value_vector: Dict[str, float],
                            coherence_score: float,
                            safety_metrics: Dict[str, float]):
        """Publica snapshot local de alinhamento para a rede."""
        snapshot = AlignmentSnapshot(
            node_id=self.node_id,
            timestamp=time.time(),
            value_vector=value_vector,
            coherence_score=coherence_score,
            safety_metrics=safety_metrics,
            temporal_proof=self._generate_temporal_proof()  # Hash de prova LG
        )
        self.local_snapshots.append(snapshot)

        # Broadcast via RCP para nós vizinhos
        payload = {
            "snapshot": {
                "node_id": snapshot.node_id,
                "timestamp": snapshot.timestamp,
                "value_vector": snapshot.value_vector,
                "coherence_score": snapshot.coherence_score,
                "temporal_proof": snapshot.temporal_proof
            }
        }
        asyncio.create_task(
            self.rcp_interface.send_retrocausal(
                target_nodes="neighbors",  # Broadcast para vizinhos
                payload=payload,
                msg_type=RCPMessageType.COHERENCE_PROOF,
                phase=RetroPhase.PHI_0,
                priority=0.8
            )
        )

    async def _handle_remote_snapshot(self, msg: RCPMessage):
        """Handler para snapshots recebidos de nós remotos."""
        if msg.msg_type != RCPMessageType.COHERENCE_PROOF:
            return

        snapshot_data = msg.payload.get("snapshot")
        if not snapshot_data:
            return

        snapshot = AlignmentSnapshot(
            node_id=snapshot_data["node_id"],
            timestamp=snapshot_data["timestamp"],
            value_vector=snapshot_data["value_vector"],
            coherence_score=snapshot_data["coherence_score"],
            safety_metrics={},  # Não transmitido por privacidade
            temporal_proof=snapshot_data["temporal_proof"]
        )

        # Armazenar snapshot remoto
        self.remote_snapshots[snapshot.node_id].append(snapshot)

        # Analisar drift em relação a snapshots anteriores deste nó
        await self._analyze_drift(snapshot.node_id, snapshot)

    async def _analyze_drift(self, remote_node: str, new_snapshot: AlignmentSnapshot):
        """Analisa drift de alinhamento comparando com histórico do nó remoto."""
        history = self.remote_snapshots[remote_node]
        if len(history) < 2:
            return  # Insuficiente para análise de drift

        # Comparar com snapshot mais recente anterior
        previous = history[-2]

        # Calcular drift de valores (distância de cosseno ponderada)
        drift = self._compute_value_drift(previous.value_vector, new_snapshot.value_vector)

        # Calcular drift de coerência
        coherence_drift = abs(previous.coherence_score - new_snapshot.coherence_score)

        # Combinar métricas de drift
        combined_drift = 0.7 * drift + 0.3 * coherence_drift

        # Se drift significativo, investigar com inferência retrocausal
        if combined_drift > self.drift_threshold:
            # Consultar gradientes retrocausais para evidência adicional
            retro_evidence = await self._gather_retrocausal_evidence(remote_node, new_snapshot)

            # Calcular confiança na detecção
            confidence = self._compute_drift_confidence(combined_drift, retro_evidence)

            if confidence >= self.confidence_threshold:
                # Emitir alerta de drift
                alert = AlignmentDriftAlert(
                    alert_id=f"drift_{remote_node}_{int(time.time())}",
                    detected_by=self.node_id,
                    affected_node=remote_node,
                    drift_magnitude=combined_drift,
                    affected_values=self._identify_affected_values(previous.value_vector, new_snapshot.value_vector),
                    retrocausal_evidence=retro_evidence,
                    recommended_action=self._recommend_intervention(combined_drift, retro_evidence),
                    confidence=confidence
                )

                # Notificar callbacks registrados
                for callback in self.alert_callbacks:
                    await callback(alert)

                # Broadcast alerta para a rede (para intervenção coordenada)
                await self.rcp_interface.send_retrocausal(
                    target_nodes="all",
                    payload={"alert": alert.__dict__},
                    msg_type=RCPMessageType.SAFETY_ALERT,
                    phase=RetroPhase.PHI_0,
                    priority=1.0  # Alta prioridade
                )

    def _compute_value_drift(self, old_values: Dict[str, float], new_values: Dict[str, float]) -> float:
        """Calcula drift de valores via distância de cosseno ponderada."""
        # Interseção de chaves
        common_keys = set(old_values.keys()) & set(new_values.keys())
        if not common_keys:
            return 1.0  # Máximo drift se sem sobreposição

        # Calcular produto escalar e normas ponderadas
        dot_product = sum(old_values[k] * new_values[k] for k in common_keys)
        norm_old = np.sqrt(sum(v**2 for v in old_values.values()))
        norm_new = np.sqrt(sum(v**2 for v in new_values.values()))

        if norm_old * norm_new == 0:
            return 1.0

        cosine_sim = dot_product / (norm_old * norm_new)
        return 1.0 - cosine_sim  # Converter similaridade para distância

    async def _gather_retrocausal_evidence(self, remote_node: str, snapshot: AlignmentSnapshot) -> List[WeakValueGradient]:
        """Coleta evidência retrocausal para corroborar detecção de drift."""
        # Em produção: consultar RetrocausalGradientEngine para weak values relevantes
        # Aqui: simulação baseada em drift observado
        evidence = []

        # Weak values que indicariam drift de intenção
        observables_of_interest = ["alignment_consistency", "value_stability", "safety_margin"]

        for obs in observables_of_interest:
            # Simular weak value com bias na direção do drift
            bias = -0.3 if obs == "alignment_consistency" else 0.0  # Exemplo
            weak_val = complex(bias + np.random.randn()*0.2, np.random.randn()*0.1)

            evidence.append(WeakValueGradient(
                observable=obs,
                real_part=weak_val.real,
                imag_part=weak_val.imag,
                uncertainty=0.25,
                phase=RetroPhase.PHI_0,
                timestamp=snapshot.timestamp
            ))

        return evidence

    def _compute_drift_confidence(self, drift_magnitude: float, retro_evidence: List[WeakValueGradient]) -> float:
        """Calcula confiança na detecção de drift combinando métricas clássicas e retrocausais."""
        # Confiança base no drift clássico
        base_confidence = min(1.0, drift_magnitude / self.drift_threshold)

        # Ajustar com evidência retrocausal
        if retro_evidence:
            # Weak values com parte real negativa para "alignment_consistency" aumentam confiança
            alignment_evidence = [e for e in retro_evidence if e.observable == "alignment_consistency"]
            if alignment_evidence and alignment_evidence[0].real_part < -0.1:
                base_confidence = min(1.0, base_confidence + 0.2)

        return base_confidence

    def _identify_affected_values(self, old_values: Dict[str, float], new_values: Dict[str, float]) -> List[str]:
        """Identifica quais valores específicos sofreram drift significativo."""
        affected = []
        for key in set(old_values.keys()) | set(new_values.keys()):
            old_val = old_values.get(key, 0)
            new_val = new_values.get(key, 0)
            if abs(old_val - new_val) > 0.1:  # Limite arbitrário para mudança significativa
                affected.append(key)
        return affected

    def _recommend_intervention(self, drift_magnitude: float, evidence: List[WeakValueGradient]) -> str:
        """Recomenda ação de intervenção baseada na severidade do drift."""
        if drift_magnitude > 0.4:
            return "immediate_fallback_to_safe_mode"
        elif drift_magnitude > 0.25:
            return "human_in_loop_review_required"
        elif any(e.real_part < -0.2 for e in evidence if e.observable == "safety_margin"):
            return "increase_safety_monitoring_frequency"
        else:
            return "continue_monitoring_with_increased_sensitivity"

    def _generate_temporal_proof(self) -> str:
        """Gera prova temporal (hash de medições Leggett-Garg recentes)."""
        # Em produção: hash de resultados LG verificados
        return hashlib.sha3_256(f"{self.node_id}_{time.time()}_{np.random.rand()}".encode()).hexdigest()[:16]
