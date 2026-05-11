# arkhe_os/mrc/cosnark_audit_trail.py
"""
Sistema de auditoria CoSNARK para rastreabilidade imutável de pacotes
com provas criptográficas federadas e verificação de integridade.
"""
import hashlib
import json
import time
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np

class AuditEventType(Enum):
    PACKET_SENT = "packet_sent"
    PACKET_RECEIVED = "packet_received"
    PACKET_TRIMMED = "packet_trimmed"
    SYNDROME_GENERATED = "syndrome_generated"
    CORRECTION_ATTEMPTED = "correction_attempted"
    ROUTE_VALIDATED = "route_validated"
    COHERENCE_UPDATED = "coherence_updated"
    CONGESTION_SIGNAL = "congestion_signal"

@dataclass
class AuditEvent:
    """Evento auditável para rastreabilidade de pacotes."""
    event_id: str
    event_type: AuditEventType
    timestamp: float
    qp_id: str
    packet_id: Optional[str]
    path_id: Optional[str]
    coherence_value: Optional[float]
    metadata: Dict[str, Any]

    # Campos para prova criptográfica
    prev_event_hash: str = ""  # Hash do evento anterior (para chaining)
    signature: str = ""         # Assinatura digital (se aplicável)

    def compute_hash(self) -> str:
        """Computa hash criptográfico do evento para merkle tree."""
        # Serializar campos relevantes (excluir signature para hashing)
        data = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'qp_id': self.qp_id,
            'packet_id': self.packet_id,
            'path_id': self.path_id,
            'coherence_value': self.coherence_value,
            'metadata': self.metadata,
            'prev_hash': self.prev_event_hash,
        }
        # Hash SHA-256 para prova
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def sign_event(self, private_key: str) -> str:
        """
        Assina evento com chave privada para autenticação.

        Em produção: usar assinatura digital real (ECDSA, Ed25519)
        Aqui: hash como proxy para demonstração
        """
        message = self.compute_hash()
        # Simular assinatura: hash(message + private_key)
        return hashlib.sha256(
            (message + private_key).encode()
        ).hexdigest()[:32]  # 128 bits para demonstração

@dataclass
class CoSNARKProof:
    """Prova CoSNARK para lote de eventos auditáveis."""
    proof_id: str
    event_range: Tuple[str, str]  # (first_event_id, last_event_id)
    merkle_root: str              # Raiz da merkle tree dos eventos
    proof_data: str               # Dados da prova ZK (simplificado)
    prover_id: str                # Identificador do prover
    timestamp: float
    coherence_aggregate: float    # Φ_C agregado dos eventos
    integrity_hash: str           # Hash de integridade da prova

    def verify_proof(self, expected_root: str) -> bool:
        """Verifica prova contra raiz merkle esperada."""
        # Em produção: verificação ZK real
        # Aqui: comparação simples de hash para demonstração
        return self.merkle_root == expected_root

class CoSNARKAuditTrail:
    """
    Sistema de auditoria com provas CoSNARK para rastreabilidade de pacotes.

    Funcionalidades:
    - Logging imutável de eventos com chaining criptográfico
    - Geração periódica de provas CoSNARK para lotes de eventos
    - Verificação federada de integridade entre nós
    - Consulta eficiente por packet_id, path_id, ou intervalo temporal
    """

    def __init__(
        self,
        node_id: str,
        batch_size: int = 100,           # Eventos por prova CoSNARK
        proof_interval: float = 10.0,    # Gerar prova a cada 10s
        retention_hours: int = 24,       # Reter eventos por 24h
        federation_nodes: Optional[List[str]] = None,  # Nós para verificação federada
    ):
        self.node_id = node_id
        self.batch_size = batch_size
        self.proof_interval = proof_interval
        self.retention_seconds = retention_hours * 3600
        self.federation_nodes = federation_nodes or []

        # Estado interno
        self.event_log: List[AuditEvent] = []
        self.event_index: Dict[str, AuditEvent] = {}  # event_id -> event
        self.proofs: List[CoSNARKProof] = []
        self.last_proof_time: float = 0.0

        # Chaves para assinatura (em produção: gerenciar via HSM/KMS)
        self.private_key = hashlib.sha256(f"{node_id}_audit_key".encode()).hexdigest()[:16]
        self.public_key = hashlib.sha256(self.private_key.encode()).hexdigest()[:16]

        # Estatísticas
        self.stats = {
            'events_logged': 0,
            'proofs_generated': 0,
            'verifications_passed': 0,
            'verifications_failed': 0,
        }

    def log_event(
        self,
        event_type: AuditEventType,
        qp_id: str,
        packet_id: Optional[str] = None,
        path_id: Optional[str] = None,
        coherence_value: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Registra evento auditável e retorna event_id.

        Implementa chaining criptográfico: cada evento referencia hash do anterior.
        """
        # Gerar event_id único
        event_id = f"{self.node_id}_{int(time.time() * 1e6)}_{len(self.event_log)}"

        # Determinar prev_event_hash
        prev_hash = self.event_log[-1].compute_hash() if self.event_log else "genesis"

        # Criar evento
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            qp_id=qp_id,
            packet_id=packet_id,
            path_id=path_id,
            coherence_value=coherence_value,
            metadata=metadata or {},
            prev_event_hash=prev_hash,
        )

        # Assinar evento
        event.signature = event.sign_event(self.private_key)

        # Adicionar ao log e índice
        self.event_log.append(event)
        self.event_index[event_id] = event
        self.stats['events_logged'] += 1

        # Verificar se é hora de gerar prova CoSNARK
        self._maybe_generate_proof()

        # Limpar eventos antigos baseado em retention
        self._cleanup_old_events()

        return event_id

    def query_events(
        self,
        packet_id: Optional[str] = None,
        path_id: Optional[str] = None,
        time_range: Optional[Tuple[float, float]] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Consulta eventos auditáveis com filtros.

        Returns:
            Lista de eventos ordenados por timestamp
        """
        results = []

        for event in reversed(self.event_log):  # Mais recentes primeiro
            # Aplicar filtros
            if packet_id and event.packet_id != packet_id:
                continue
            if path_id and event.path_id != path_id:
                continue
            if time_range:
                if not (time_range[0] <= event.timestamp <= time_range[1]):
                    continue
            if event_types and event.event_type not in event_types:
                continue

            results.append(event)
            if len(results) >= limit:
                break

        return results

    def generate_cosnark_proof(
        self,
        start_event_id: Optional[str] = None,
        end_event_id: Optional[str] = None,
    ) -> Optional[CoSNARKProof]:
        """
        Gera prova CoSNARK para lote de eventos.

        Em produção: usar proving system real (Groth16, PLONK, etc.)
        Aqui: simulação com merkle tree + hash agregado
        """
        # Determinar range de eventos
        if not start_event_id:
            start_idx = 0
        else:
            start_idx = next(
                (i for i, e in enumerate(self.event_log) if e.event_id == start_event_id),
                0
            )

        if not end_event_id:
            end_idx = min(start_idx + self.batch_size, len(self.event_log))
        else:
            end_idx = next(
                (i for i, e in enumerate(self.event_log) if e.event_id == end_event_id),
                len(self.event_log) - 1
            )
            end_idx = min(end_idx + 1, len(self.event_log))

        events_batch = self.event_log[start_idx:end_idx]
        if not events_batch:
            return None

        # Construir merkle tree dos eventos
        merkle_root = self._build_merkle_tree(events_batch)

        # Calcular coerência agregada
        coherence_values = [
            e.coherence_value for e in events_batch
            if e.coherence_value is not None
        ]
        avg_coherence = np.mean(coherence_values) if coherence_values else 0.0

        # Gerar proof_id
        proof_id = f"proof_{self.node_id}_{int(time.time())}_{len(self.proofs)}"

        # Criar prova (simulada)
        proof = CoSNARKProof(
            proof_id=proof_id,
            event_range=(events_batch[0].event_id, events_batch[-1].event_id),
            merkle_root=merkle_root,
            proof_data=self._generate_proof_data(events_batch, merkle_root),
            prover_id=self.node_id,
            timestamp=time.time(),
            coherence_aggregate=avg_coherence,
            integrity_hash=hashlib.sha256(
                f"{merkle_root}{avg_coherence}{proof_id}".encode()
            ).hexdigest(),
        )

        # Assinar prova
        proof.proof_data = hashlib.sha256(
            (proof.proof_data + self.private_key).encode()
        ).hexdigest()[:32]

        # Armazenar prova
        self.proofs.append(proof)
        self.last_proof_time = time.time()
        self.stats['proofs_generated'] += 1

        return proof

    def verify_proof_federated(
        self,
        proof: CoSNARKProof,
        expected_root: str,
    ) -> Tuple[bool, str]:
        """
        Verifica prova CoSNARK com validação federada.

        Returns:
            (is_valid, reason)
        """
        # Verificação local da prova
        if not proof.verify_proof(expected_root):
            self.stats['verifications_failed'] += 1
            return False, "Merkle root mismatch"

        # Verificação federada: consultar outros nós
        if self.federation_nodes:
            # Em produção: RPC para outros nós verificarem prova
            # Aqui: simular consenso simples
            consensus_threshold = len(self.federation_nodes) // 2 + 1
            verified_count = 1  # Nós locais sempre contam

            for peer in self.federation_nodes:
                # Simular verificação remota (90% de sucesso para demo)
                if random.random() < 0.9:
                    verified_count += 1
                    if verified_count >= consensus_threshold:
                        break

            if verified_count < consensus_threshold:
                self.stats['verifications_failed'] += 1
                return False, f"Federated consensus failed: {verified_count}/{len(self.federation_nodes) + 1}"

        self.stats['verifications_passed'] += 1
        return True, "Proof verified successfully"

    def export_audit_report(
        self,
        time_range: Tuple[float, float],
        include_proofs: bool = True,
    ) -> Dict:
        """
        Exporta relatório de auditoria para compliance.

        Formato compatível com sistemas de logging federados.
        """
        # Filtrar eventos no intervalo
        events = [
            e for e in self.event_log
            if time_range[0] <= e.timestamp <= time_range[1]
        ]

        # Filtrar provas relevantes
        relevant_proofs = []
        if include_proofs:
            for proof in self.proofs:
                # Verificar se proof cobre algum evento no intervalo
                if any(
                    time_range[0] <= self.event_index[eid].timestamp <= time_range[1]
                    for eid in [proof.event_range[0], proof.event_range[1]]
                    if eid in self.event_index
                ):
                    relevant_proofs.append({
                        'proof_id': proof.proof_id,
                        'merkle_root': proof.merkle_root,
                        'coherence_aggregate': proof.coherence_aggregate,
                        'timestamp': proof.timestamp,
                        'prover_id': proof.prover_id,
                    })

        # Calcular métricas agregadas
        coherence_values = [e.coherence_value for e in events if e.coherence_value]

        return {
            'report_id': hashlib.sha256(
                f"{self.node_id}_{time_range[0]}_{time_range[1]}".encode()
            ).hexdigest()[:16],
            'node_id': self.node_id,
            'time_range': {
                'start': time_range[0],
                'end': time_range[1],
            },
            'summary': {
                'total_events': len(events),
                'event_types': {
                    et.value: sum(1 for e in events if e.event_type == et)
                    for et in AuditEventType
                },
                'avg_coherence': round(np.mean(coherence_values), 4) if coherence_values else None,
                'coherence_std': round(np.std(coherence_values), 4) if coherence_values else None,
            },
            'events': [
                {
                    'event_id': e.event_id,
                    'type': e.event_type.value,
                    'timestamp': e.timestamp,
                    'qp_id': e.qp_id,
                    'packet_id': e.packet_id,
                    'path_id': e.path_id,
                    'coherence': e.coherence_value,
                    'hash': e.compute_hash(),
                }
                for e in events
            ],
            'proofs': relevant_proofs,
            'integrity': {
                'merkle_root_latest': self._build_merkle_tree(self.event_log[-10:]) if self.event_log else None,
                'public_key': self.public_key,
                'federation_nodes': self.federation_nodes,
            },
            'stats': self.stats,
        }

    def _maybe_generate_proof(self):
        """Gera prova CoSNARK se intervalo foi atingido."""
        if time.time() - self.last_proof_time >= self.proof_interval:
            if len(self.event_log) >= self.batch_size:
                self.generate_cosnark_proof()

    def _cleanup_old_events(self):
        """Remove eventos antigos baseado em política de retenção."""
        cutoff = time.time() - self.retention_seconds
        # Manter apenas eventos recentes
        self.event_log = [e for e in self.event_log if e.timestamp > cutoff]
        # Atualizar índice
        self.event_index = {e.event_id: e for e in self.event_log}

    def _build_merkle_tree(self, events: List[AuditEvent]) -> str:
        """Constrói raiz de merkle tree para lote de eventos."""
        if not events:
            return hashlib.sha256(b"empty").hexdigest()

        # Hashes das folhas
        hashes = [e.compute_hash() for e in events]

        # Construir tree bottom-up
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicar último se ímpar

            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = next_level

        return hashes[0]

    def _generate_proof_data(
        self,
        events: List[AuditEvent],
        merkle_root: str,
    ) -> str:
        """
        Gera dados de prova CoSNARK (simulado).

        Em produção: gerar proof real usando proving system.
        """
        # Dados simplificados para demonstração
        proof_data = {
            'num_events': len(events),
            'merkle_root': merkle_root,
            'coherence_stats': {
                'min': min((e.coherence_value for e in events if e.coherence_value), default=0),
                'max': max((e.coherence_value for e in events if e.coherence_value), default=1),
                'mean': np.mean([e.coherence_value for e in events if e.coherence_value]) if any(e.coherence_value for e in events) else 0,
            },
            'timestamp': time.time(),
        }
        return json.dumps(proof_data, sort_keys=True)

    def get_audit_stats(self) -> Dict:
        """Retorna estatísticas de auditoria para monitoramento."""
        return {
            **self.stats,
            'pending_events': len(self.event_log),
            'cached_proofs': len(self.proofs),
            'last_proof_time': self.last_proof_time,
            'retention_cutoff': time.time() - self.retention_seconds,
        }
