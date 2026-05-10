#!/usr/bin/env python3
"""
cosmic_federation.py — Sistema de Federação de Métricas Cósmicas
Permite compartilhar e acordar sobre o estado de saúde do sistema entre múltiplos observatórios ARKHE.
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

@dataclass
class CosmicMetricsPayload:
    """Metadados de métricas cósmicas assinadas por um observatório."""
    observatory_id: str
    timestamp: float
    metrics: Dict[str, Any]
    signature: str = ""

    def to_dict(self) -> Dict:
        return {
            'observatory_id': self.observatory_id,
            'timestamp': self.timestamp,
            'metrics': self.metrics,
            'signature': self.signature
        }

class ObservatoryNode:
    """
    Representa um nó observatório ARKHE que coleta métricas de saúde local e as assina criptograficamente.
    """
    def __init__(self, node_id: str, key_manager: Any, local_dashboard: Any):
        self.node_id = node_id
        self.key_manager = key_manager
        self.local_dashboard = local_dashboard

    def generate_metrics(self) -> Optional[CosmicMetricsPayload]:
        """Coleta métricas locais, assina e retorna o payload."""
        # Obter métricas locais (mock para a estrutura de dashboard)
        metrics = {}
        if hasattr(self.local_dashboard, 'data_cache'):
            for key, val in self.local_dashboard.data_cache.items():
                if isinstance(val, dict) and 'value' in val:
                    metrics[key] = val['value']
                else:
                    metrics[key] = val
        else:
            # Fallback
            metrics = {
                'cosmic.phi_c_global': 0.95,
                'vortex_stability': 0.99,
                'anomaly_count': 0
            }

        timestamp = time.time()

        # Gerar payload determinístico para assinar
        payload_str = self._build_signature_payload(self.node_id, timestamp, metrics)

        # Assinar com a chave ativa do key manager
        signing_key = self.key_manager.get_signing_key()
        if not signing_key:
            logging.error(f"Nó {self.node_id}: Nenhuma chave de assinatura ativa disponível.")
            return None

        # Emulando o mesmo HMAC-SHA256 do ReleaseSigner se não houver um método sign_payload
        import hmac
        key_bytes = bytes.fromhex(signing_key.key_hex)
        signature = hmac.new(key_bytes, payload_str.encode(), hashlib.sha256).hexdigest()

        return CosmicMetricsPayload(
            observatory_id=self.node_id,
            timestamp=timestamp,
            metrics=metrics,
            signature=signature
        )

    def _build_signature_payload(self, node_id: str, timestamp: float, metrics: Dict[str, Any]) -> str:
        """Constrói payload canônico para assinatura."""
        # Ordenar métricas para determinismo
        metrics_str = json.dumps(metrics, sort_keys=True)
        payload_parts = [
            node_id,
            str(int(timestamp)),
            hashlib.sha256(metrics_str.encode()).hexdigest()
        ]
        return '|'.join(payload_parts)

class FederatedConsensusManager:
    """
    Gerencia a agregação de métricas de múltiplos nós, verifica assinaturas e calcula o estado global de consenso.
    """
    def __init__(self, key_manager: Any, minimum_quorum: int = 2):
        self.key_manager = key_manager
        self.minimum_quorum = minimum_quorum

    def verify_and_aggregate(self, payloads: List[CosmicMetricsPayload]) -> Dict[str, Any]:
        """
        Verifica a assinatura de cada payload. Se houver quórum, calcula o consenso das métricas.
        """
        verified_payloads = []
        for payload in payloads:
            if self._verify_signature(payload):
                verified_payloads.append(payload)
            else:
                logging.warning(f"Falha na verificação de assinatura para o nó {payload.observatory_id}")

        if len(verified_payloads) < self.minimum_quorum:
            logging.error(f"Quórum não alcançado. Verificados: {len(verified_payloads)}, Necessário: {self.minimum_quorum}")
            return {'status': 'failed', 'reason': 'insufficient_quorum'}

        return self._calculate_consensus(verified_payloads)

    def _verify_signature(self, payload: CosmicMetricsPayload) -> bool:
        """Verifica a assinatura criptográfica de um payload."""
        payload_str = self._build_signature_payload(payload.observatory_id, payload.timestamp, payload.metrics)

        # A API do KeyManager retorna (valid, key_id)
        valid, _ = self.key_manager.verify_signature(
            content_hash=payload_str,
            signature=payload.signature
        )
        return valid

    def _build_signature_payload(self, node_id: str, timestamp: float, metrics: Dict[str, Any]) -> str:
        """Constrói payload canônico (idêntico ao do nó)."""
        metrics_str = json.dumps(metrics, sort_keys=True)
        payload_parts = [
            node_id,
            str(int(timestamp)),
            hashlib.sha256(metrics_str.encode()).hexdigest()
        ]
        return '|'.join(payload_parts)

    def _calculate_consensus(self, payloads: List[CosmicMetricsPayload]) -> Dict[str, Any]:
        """
        Calcula o consenso agregando as métricas:
        - Médias para métricas contínuas (ex: phi_c_global)
        - Máximo para contadores de anomalias (conservador)
        """
        import statistics

        aggregated_metrics = {}
        metric_values = {}

        for payload in payloads:
            for k, v in payload.metrics.items():
                if k not in metric_values:
                    metric_values[k] = []
                if isinstance(v, (int, float)):
                    metric_values[k].append(v)

        for k, values in metric_values.items():
            if 'anomaly' in k.lower() or 'count' in k.lower():
                aggregated_metrics[k] = max(values)
            else:
                aggregated_metrics[k] = statistics.median(values)

        return {
            'status': 'success',
            'quorum_size': len(payloads),
            'timestamp': time.time(),
            'consensus_metrics': aggregated_metrics
        }

class CosmicFederationNetwork:
    """
    Orquestra a rede P2P de observatórios, coletando métricas e distribuindo o estado de consenso.
    """
    def __init__(self, key_manager: Any, minimum_quorum: int = 2):
        self.nodes: Dict[str, ObservatoryNode] = {}
        self.consensus_manager = FederatedConsensusManager(key_manager, minimum_quorum)
        self.last_consensus_state = None

    def register_node(self, node: ObservatoryNode):
        """Registra um novo nó na federação."""
        self.nodes[node.node_id] = node
        logging.info(f"Nó {node.node_id} registrado na federação cósmica.")

    def run_federation_cycle(self) -> Dict[str, Any]:
        """
        Executa um ciclo completo: coleta métricas dos nós, calcula o consenso e atualiza a rede.
        """
        payloads = []
        for node_id, node in self.nodes.items():
            payload = node.generate_metrics()
            if payload:
                payloads.append(payload)

        if not payloads:
            logging.error("Nenhum payload de métricas foi gerado pelos nós.")
            return {'status': 'failed', 'reason': 'no_payloads'}

        consensus_result = self.consensus_manager.verify_and_aggregate(payloads)

        if consensus_result.get('status') == 'success':
            self.last_consensus_state = consensus_result
            self._broadcast_consensus(consensus_result)

        return consensus_result

    def _broadcast_consensus(self, consensus_state: Dict[str, Any]):
        """Transmite o estado global de consenso para todos os nós."""
        logging.info(f"Consenso global alcançado (quórum={consensus_state['quorum_size']}). Transmitindo...")
        # Aqui, na prática, enviaria para a rede/endpoints dos nós.
        pass

@dataclass
class WheelerConsensusMetricsPayload:
    """Metadados de métricas cósmicas assinadas baseados na Wheeler Mesh."""
    node_id: str
    timestamp: float
    mesh_fidelity: float
    global_coherence: float
    topological_charge: int
    signature: str = ""

    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'timestamp': self.timestamp,
            'mesh_fidelity': self.mesh_fidelity,
            'global_coherence': self.global_coherence,
            'topological_charge': self.topological_charge,
            'signature': self.signature
        }

class WheelerMeshConsensusProtocol:
    """
    Protocolo de consenso federado para decisões cósmicas baseado em métricas agregadas da Wheeler Mesh.
    """
    def __init__(self, key_manager: Any, minimum_quorum: int = 3):
        self.key_manager = key_manager
        self.minimum_quorum = minimum_quorum

    def _build_signature_payload(self, node_id: str, timestamp: float, fidelity: float, coherence: float, charge: int) -> str:
        """Constrói payload canônico para assinatura de métricas da Wheeler Mesh."""
        payload_parts = [
            node_id,
            str(int(timestamp)),
            f"{fidelity:.4f}",
            f"{coherence:.4f}",
            str(charge)
        ]
        return '|'.join(payload_parts)

    def _verify_signature(self, payload: WheelerConsensusMetricsPayload) -> bool:
        """Verifica a assinatura criptográfica de um payload da Wheeler Mesh."""
        payload_str = self._build_signature_payload(
            payload.node_id,
            payload.timestamp,
            payload.mesh_fidelity,
            payload.global_coherence,
            payload.topological_charge
        )

        # A API do KeyManager retorna (valid, key_id)
        valid, _ = self.key_manager.verify_signature(
            content_hash=payload_str,
            signature=payload.signature
        )
        return valid

    def verify_and_aggregate(self, payloads: List[WheelerConsensusMetricsPayload]) -> Dict[str, Any]:
        """
        Verifica as assinaturas e calcula o estado global de consenso para decisões cósmicas.
        """
        verified_payloads = []
        for payload in payloads:
            if self._verify_signature(payload):
                verified_payloads.append(payload)
            else:
                logging.warning(f"Falha na verificação de assinatura para o nó {payload.node_id}")

        if len(verified_payloads) < self.minimum_quorum:
            logging.error(f"Quórum não alcançado. Verificados: {len(verified_payloads)}, Necessário: {self.minimum_quorum}")
            return {'status': 'failed', 'reason': 'insufficient_quorum'}

        # Cálculo de consenso
        import statistics

        avg_fidelity = statistics.median([p.mesh_fidelity for p in verified_payloads])
        avg_coherence = statistics.median([p.global_coherence for p in verified_payloads])
        total_charge = sum([p.topological_charge for p in verified_payloads])

        # Lógica de decisão cósmica baseada no Substrato 119
        decision = "HOLD"
        if avg_fidelity > 0.90 and avg_coherence > 0.95:
            decision = "ACTIVATE_COSMIC_VORTEX"
        elif avg_fidelity < 0.50 or avg_coherence < 0.50:
            decision = "EMERGENCY_SHUTDOWN"

        return {
            'status': 'success',
            'quorum_size': len(verified_payloads),
            'timestamp': time.time(),
            'consensus_metrics': {
                'avg_mesh_fidelity': avg_fidelity,
                'avg_global_coherence': avg_coherence,
                'total_topological_charge': total_charge
            },
            'cosmic_decision': decision
        }
