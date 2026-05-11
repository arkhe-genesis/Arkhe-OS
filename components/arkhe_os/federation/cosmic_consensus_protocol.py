#!/usr/bin/env python3
"""
cosmic_consensus_protocol.py — Protocolo de consenso distribuído para métricas cósmicas.
Implementa BFT adaptativo com tolerância a falhas bizantinas para federação de observatórios.
"""

import asyncio
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import logging
import numpy as np

class ConsensusPhase(Enum):
    """Fases do protocolo de consenso BFT."""
    PREPREPARE = auto()
    PREPARE = auto()
    COMMIT = auto()
    DECIDE = auto()
    ABORT = auto()

class NodeRole(Enum):
    """Papéis dos nós na federação."""
    PRIMARY = auto()      # Líder atual do consenso
    VALIDATOR = auto()    # Validador com direito a voto
    OBSERVER = auto()     # Observador sem direito a voto (apenas replica)
    SUSPECT = auto()      # Nó sob investigação por comportamento suspeito

@dataclass
class CosmicMetricProposal:
    """Proposta de métrica para consenso federado."""
    proposal_id: str
    metric_name: str
    metric_value: float
    metric_metadata: Dict[str, Any]
    proposer_node_id: str
    timestamp: float
    signature: str  # Assinatura criptográfica da proposta
    epoch: int  # Epoch do consenso para ordenação total

    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_metadata': self.metric_metadata,
            'proposer_node_id': self.proposer_node_id,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'epoch': self.epoch
        }

    def compute_hash(self) -> str:
        """Computa hash canônico da proposta para consenso."""
        canonical = json.dumps({
            'proposal_id': self.proposal_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'proposer_node_id': self.proposer_node_id,
            'epoch': self.epoch
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

@dataclass
class ConsensusMessage:
    """Mensagem trocada durante protocolo de consenso."""
    msg_id: str
    phase: ConsensusPhase
    proposal_hash: str
    sender_node_id: str
    signature: str
    timestamp: float
    epoch: int
    view_number: int  # Para view changes em caso de falha do líder

    def to_dict(self) -> Dict:
        return {
            'msg_id': self.msg_id,
            'phase': self.phase.name,
            'proposal_hash': self.proposal_hash,
            'sender_node_id': self.sender_node_id,
            'signature': self.signature,
            'timestamp': self.timestamp,
            'epoch': self.epoch,
            'view_number': self.view_number
        }

class CosmicConsensusProtocol:
    """
    Protocolo de consenso BFT adaptativo para métricas cósmicas federadas.
    Características:
    - Tolerância a f falhas bizantinas com n >= 3f + 1 nós
    - View change automático em caso de líder lento ou malicioso
    - Ordenação total de propostas via epoch + sequência
    - Assinaturas criptográficas em todas as mensagens
    """

    def __init__(
        self,
        node_id: str,
        federation_config: Dict[str, Any],
        key_manager: Optional['KeyManager'] = None,
        metric_validator: Optional[Callable[[CosmicMetricProposal], bool]] = None
    ):
        self.node_id = node_id
        self.config = federation_config
        self.key_manager = key_manager
        self.metric_validator = metric_validator or (lambda p: True)

        # Estado do consenso
        self.current_epoch = 0
        self.current_view = 0
        self.current_phase = ConsensusPhase.PREPREPARE
        self.primary_node_id: Optional[str] = None

        # Conjuntos de nós por papel
        self.validators: Set[str] = set(federation_config.get('validators', []))
        self.observers: Set[str] = set(federation_config.get('observers', []))
        self.suspects: Set[str] = set()

        # Buffers de mensagens por fase
        self.preprepare_buffer: Dict[str, CosmicMetricProposal] = {}
        self.prepare_buffer: Dict[str, Dict[str, ConsensusMessage]] = defaultdict(dict)
        self.commit_buffer: Dict[str, Dict[str, ConsensusMessage]] = defaultdict(dict)

        # Propostas decididas
        self.decided_proposals: Dict[str, CosmicMetricProposal] = {}

        # Callbacks para notificação
        self.consensus_callbacks: List[Callable] = []

        # Métricas de consenso
        self.consensus_metrics = {
            'proposals_received': 0,
            'consensus_rounds_completed': 0,
            'view_changes_triggered': 0,
            'byzantine_detections': 0,
            'avg_consensus_latency_ms': 0.0
        }

        # Timer para view change
        self.view_change_timeout_sec = federation_config.get('view_change_timeout_sec', 10.0)
        self.last_primary_activity: Dict[str, float] = {}

        logging.info(f"✅ CosmicConsensusProtocol initialized: node={node_id}, validators={len(self.validators)}")

    def _select_primary(self, epoch: int) -> str:
        """Seleciona nó primário para epoch baseado em rotação determinística."""
        validator_list = sorted(list(self.validators))
        return validator_list[epoch % len(validator_list)]

    def _verify_message_signature(self, msg: ConsensusMessage) -> bool:
        """Verifica assinatura criptográfica de mensagem de consenso."""
        if not self.key_manager:
            return True  # Modo desenvolvimento sem criptografia

        # Reconstruir payload canônico para verificação
        payload = json.dumps({
            'msg_id': msg.msg_id,
            'phase': msg.phase.name,
            'proposal_hash': msg.proposal_hash,
            'sender_node_id': msg.sender_node_id,
            'timestamp': msg.timestamp,
            'epoch': msg.epoch,
            'view_number': msg.view_number
        }, sort_keys=True)

        return self.key_manager.verify_signature(
            content_hash=payload,
            signature=msg.signature,
            signer_node_id=msg.sender_node_id
        )

    async def propose_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_metadata: Dict[str, Any]
    ) -> Optional[CosmicMetricProposal]:
        """
        Propõe nova métrica para consenso federado.
        Apenas nós primários podem iniciar proposta.
        """
        if self.node_id != self._select_primary(self.current_epoch):
            logging.warning(f"⚠️ Node {self.node_id} not primary — cannot propose")
            return None

        # Criar proposta
        proposal = CosmicMetricProposal(
            proposal_id=hashlib.sha256(
                f"{metric_name}:{metric_value}:{time.time()}".encode()
            ).hexdigest()[:16],
            metric_name=metric_name,
            metric_value=metric_value,
            metric_metadata=metric_metadata,
            proposer_node_id=self.node_id,
            timestamp=time.time(),
            signature='',  # Preenchido abaixo
            epoch=self.current_epoch
        )

        # Assinar proposta
        if self.key_manager:
            payload = json.dumps(proposal.to_dict(), sort_keys=True)
            proposal.signature = self.key_manager.sign_content(payload)

        # Validar proposta localmente
        if not self.metric_validator(proposal):
            logging.warning(f"⚠️ Proposal failed local validation: {proposal.proposal_id}")
            return None

        # Fase PRE-PREPARE: enviar para todos os validadores
        await self._broadcast_preprepare(proposal)

        logging.info(f"📢 Proposta iniciada: {proposal.proposal_id} (epoch={self.current_epoch})")
        return proposal

    async def _broadcast_preprepare(self, proposal: CosmicMetricProposal):
        """Fase PRE-PREPARE: primário envia proposta para validadores."""
        proposal_hash = proposal.compute_hash()
        self.preprepare_buffer[proposal_hash] = proposal

        # Criar mensagem PRE-PREPARE
        msg = ConsensusMessage(
            msg_id=f"preprepare-{proposal_hash}",
            phase=ConsensusPhase.PREPREPARE,
            proposal_hash=proposal_hash,
            sender_node_id=self.node_id,
            signature='',  # Assinar se key_manager disponível
            timestamp=time.time(),
            epoch=self.current_epoch,
            view_number=self.current_view
        )

        if self.key_manager:
            payload = json.dumps(msg.to_dict(), sort_keys=True)
            msg.signature = self.key_manager.sign_content(payload)

        # Enviar para todos os validadores (exceto si mesmo)
        for validator_id in self.validators:
            if validator_id != self.node_id:
                await self._send_message(validator_id, msg)

        # Primário também envia PREPARE para si mesmo
        await self._handle_prepare(msg)

    async def _send_message(self, target_node_id: str, msg: ConsensusMessage):
        """Envia mensagem de consenso para nó específico."""
        # Em produção: enviar via rede P2P com retry e autenticação
        logging.debug(f"📤 Envia {msg.phase.name} para {target_node_id}: {msg.msg_id[:8]}")

        # Simular latência de rede
        await asyncio.sleep(0.01)

        # Em produção: chamar callback de rede real
        # await network_layer.send(target_node_id, msg.to_dict())

    async def _handle_preprepare(self, msg: ConsensusMessage, proposal: CosmicMetricProposal):
        """Manipula mensagem PRE-PREPARE recebida."""
        if not self._verify_message_signature(msg):
            logging.warning(f"❌ Assinatura inválida em PRE-PREPARE de {msg.sender_node_id}")
            return

        if msg.epoch != self.current_epoch or msg.view_number != self.current_view:
            logging.debug(f"⏭️ Mensagem de epoch/view diferente — ignorando")
            return

        proposal_hash = proposal.compute_hash()

        # Validar proposta
        if not self.metric_validator(proposal):
            logging.warning(f"⚠️ Proposal {proposal_hash} failed validation")
            return

        # Armazenar proposta
        self.preprepare_buffer[proposal_hash] = proposal
        self.consensus_metrics['proposals_received'] += 1

        # Fase PREPARE: enviar preparação para todos
        prepare_msg = ConsensusMessage(
            msg_id=f"prepare-{proposal_hash}",
            phase=ConsensusPhase.PREPARE,
            proposal_hash=proposal_hash,
            sender_node_id=self.node_id,
            signature='',
            timestamp=time.time(),
            epoch=self.current_epoch,
            view_number=self.current_view
        )

        if self.key_manager:
            payload = json.dumps(prepare_msg.to_dict(), sort_keys=True)
            prepare_msg.signature = self.key_manager.sign_content(payload)

        for validator_id in self.validators:
            if validator_id != self.node_id:
                await self._send_message(validator_id, prepare_msg)

        # Processar própria preparação
        await self._handle_prepare(prepare_msg)

    async def _handle_prepare(self, msg: ConsensusMessage):
        """Manipula mensagem PREPARE recebida."""
        if not self._verify_message_signature(msg):
            return

        if msg.epoch != self.current_epoch or msg.view_number != self.current_view:
            return

        proposal_hash = msg.proposal_hash

        # Verificar se temos a proposta correspondente
        if proposal_hash not in self.preprepare_buffer:
            logging.debug(f"⏳ Aguardando proposta para {proposal_hash[:8]}")
            return

        # Armazenar mensagem PREPARE
        self.prepare_buffer[proposal_hash][msg.sender_node_id] = msg

        # Verificar quórum de PREPARE: 2f + 1 validadores
        f = (len(self.validators) - 1) // 3  # Máximo de falhas bizantinas
        quorum_prepare = 2 * f + 1

        if len(self.prepare_buffer[proposal_hash]) >= quorum_prepare:
            # Quórum atingido: enviar COMMIT
            await self._broadcast_commit(proposal_hash)

    async def _broadcast_commit(self, proposal_hash: str):
        """Fase COMMIT: enviar commit para todos os validadores."""
        commit_msg = ConsensusMessage(
            msg_id=f"commit-{proposal_hash}",
            phase=ConsensusPhase.COMMIT,
            proposal_hash=proposal_hash,
            sender_node_id=self.node_id,
            signature='',
            timestamp=time.time(),
            epoch=self.current_epoch,
            view_number=self.current_view
        )

        if self.key_manager:
            payload = json.dumps(commit_msg.to_dict(), sort_keys=True)
            commit_msg.signature = self.key_manager.sign_content(payload)

        for validator_id in self.validators:
            if validator_id != self.node_id:
                await self._send_message(validator_id, commit_msg)

        # Processar próprio commit
        await self._handle_commit(commit_msg)

    async def _handle_commit(self, msg: ConsensusMessage):
        """Manipula mensagem COMMIT recebida."""
        if not self._verify_message_signature(msg):
            return

        if msg.epoch != self.current_epoch or msg.view_number != self.current_view:
            return

        proposal_hash = msg.proposal_hash

        if proposal_hash not in self.preprepare_buffer:
            return

        # Armazenar mensagem COMMIT
        self.commit_buffer[proposal_hash][msg.sender_node_id] = msg

        # Verificar quórum de COMMIT: 2f + 1 validadores
        f = (len(self.validators) - 1) // 3
        quorum_commit = 2 * f + 1

        if len(self.commit_buffer[proposal_hash]) >= quorum_commit:
            # Consenso alcançado!
            await self._decide_proposal(proposal_hash)

    async def _decide_proposal(self, proposal_hash: str):
        """Finaliza consenso e decide proposta."""
        if proposal_hash in self.decided_proposals:
            return  # Já decidido

        proposal = self.preprepare_buffer[proposal_hash]
        self.decided_proposals[proposal_hash] = proposal

        # Atualizar métricas
        self.consensus_metrics['consensus_rounds_completed'] += 1

        # Notificar callbacks
        for callback in self.consensus_callbacks:
            try:
                callback({
                    'type': 'consensus_decided',
                    'proposal': proposal.to_dict(),
                    'node_id': self.node_id,
                    'timestamp': time.time()
                })
            except Exception as e:
                logging.error(f"⚠️ Consensus callback error: {e}")

        logging.info(f"✅ Consenso alcançado: {proposal.metric_name} = {proposal.metric_value}")

        # Avançar epoch para próxima proposta
        self.current_epoch += 1
        self._cleanup_old_buffers()

    def _cleanup_old_buffers(self):
        """Limpa buffers de mensagens de epochs antigos."""
        # Manter apenas buffers do epoch atual e anterior
        old_epochs = [
            epoch for epoch in [
                p.epoch for p in self.preprepare_buffer.values()
            ] + [
                msg.epoch for msgs in self.prepare_buffer.values() for msg in msgs.values()
            ] + [
                msg.epoch for msgs in self.commit_buffer.values() for msg in msgs.values()
            ]
            if epoch < self.current_epoch - 1
        ]

        # Limpar propostas antigas
        self.preprepare_buffer = {
            h: p for h, p in self.preprepare_buffer.items()
            if p.epoch >= self.current_epoch - 1
        }

        # Limpar buffers de mensagens antigas
        self.prepare_buffer = {
            h: {n: m for n, m in msgs.items() if m.epoch >= self.current_epoch - 1}
            for h, msgs in self.prepare_buffer.items()
            if any(m.epoch >= self.current_epoch - 1 for m in msgs.values())
        }

        self.commit_buffer = {
            h: {n: m for n, m in msgs.items() if m.epoch >= self.current_epoch - 1}
            for h, msgs in self.commit_buffer.items()
            if any(m.epoch >= self.current_epoch - 1 for m in msgs.values())
        }

    async def trigger_view_change(self, reason: str = 'primary_timeout'):
        """Dispara mudança de view em caso de líder falho."""
        logging.warning(f"🔄 View change triggered: {reason}")
        self.consensus_metrics['view_changes_triggered'] += 1

        # Avançar view e selecionar novo primário
        self.current_view += 1
        self.primary_node_id = self._select_primary(self.current_epoch)

        # Resetar buffers para nova view
        self.preprepare_buffer.clear()
        self.prepare_buffer.clear()
        self.commit_buffer.clear()

        # Notificar mudança de view
        for callback in self.consensus_callbacks:
            try:
                callback({
                    'type': 'view_changed',
                    'old_view': self.current_view - 1,
                    'new_view': self.current_view,
                    'new_primary': self.primary_node_id,
                    'reason': reason
                })
            except Exception:
                pass

    def register_consensus_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos de consenso."""
        self.consensus_callbacks.append(callback)

    def get_consensus_status(self) -> Dict[str, Any]:
        """Retorna status atual do protocolo de consenso."""
        return {
            'node_id': self.node_id,
            'role': NodeRole.VALIDATOR.name if self.node_id in self.validators else NodeRole.OBSERVER.name,
            'current_epoch': self.current_epoch,
            'current_view': self.current_view,
            'primary_node_id': self.primary_node_id,
            'validators_count': len(self.validators),
            'decided_proposals_count': len(self.decided_proposals),
            'metrics': self.consensus_metrics,
            'pending_proposals': len(self.preprepare_buffer)
        }

    def get_decided_metrics(self, metric_name: Optional[str] = None) -> List[Dict]:
        """Retorna métricas já decididas por consenso, opcionalmente filtradas."""
        results = []
        for proposal in self.decided_proposals.values():
            if metric_name is None or proposal.metric_name == metric_name:
                results.append(proposal.to_dict())
        return sorted(results, key=lambda p: p['epoch'], reverse=True)
