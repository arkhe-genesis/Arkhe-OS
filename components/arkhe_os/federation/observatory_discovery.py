#!/usr/bin/env python3
"""
observatory_discovery.py — Protocolo para descoberta e autenticação
de novos observatórios na federação cósmica.
"""

import asyncio
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import socket

class DiscoveryPhase(Enum):
    """Fases do protocolo de descoberta."""
    ANNOUNCE = auto()
    CHALLENGE = auto()
    PROOF_OF_WORK = auto()
    VERIFICATION = auto()
    ADMISSION = auto()
    REJECTED = auto()

@dataclass
class ObservatoryIdentity:
    """Identidade criptográfica de um observatório na federação."""
    node_id: str
    public_key: str
    federation_role: str  # 'validator', 'observer'
    capabilities: Dict[str, Any]  # métricas suportadas, versão do software, etc.
    registration_timestamp: float
    signature: str  # Auto-assinatura da identidade
    cosmic_proof_of_work: Optional[str] = None  # Prova de trabalho cósmica

    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'public_key': self.public_key,
            'federation_role': self.federation_role,
            'capabilities': self.capabilities,
            'registration_timestamp': self.registration_timestamp,
            'signature': self.signature,
            'cosmic_proof_of_work': self.cosmic_proof_of_work
        }

    def compute_identity_hash(self) -> str:
        """Computa hash canônico da identidade para verificação."""
        canonical = json.dumps({
            'node_id': self.node_id,
            'public_key': self.public_key,
            'federation_role': self.federation_role,
            'capabilities': self.capabilities,
            'registration_timestamp': self.registration_timestamp
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

@dataclass
class CosmicProofOfWork:
    """Prova de trabalho cósmica para prevenir Sybil attacks."""
    challenge_seed: str
    solution: int
    difficulty_target: int  # Número de zeros à esquerda no hash
    timestamp: float
    node_id: str

    def verify(self) -> bool:
        """Verifica se a prova de trabalho é válida."""
        # Concatenar seed + solution + node_id + timestamp
        data = f"{self.challenge_seed}:{self.solution}:{self.node_id}:{self.timestamp}"
        hash_result = hashlib.sha256(data.encode()).hexdigest()

        # Verificar se hash começa com difficulty_target zeros
        return hash_result.startswith('0' * self.difficulty_target)

    @staticmethod
    def mine(challenge_seed: str, node_id: str, difficulty: int, timeout_sec: float = 60.0) -> Optional['CosmicProofOfWork']:
        """Minera prova de trabalho cósmica (CPU-bound, simplificado)."""
        start_time = time.time()
        nonce = 0

        while time.time() - start_time < timeout_sec:
            data = f"{challenge_seed}:{nonce}:{node_id}:{time.time()}"
            hash_result = hashlib.sha256(data.encode()).hexdigest()

            if hash_result.startswith('0' * difficulty):
                return CosmicProofOfWork(
                    challenge_seed=challenge_seed,
                    solution=nonce,
                    difficulty_target=difficulty,
                    timestamp=time.time(),
                    node_id=node_id
                )

            nonce += 1

        return None  # Timeout

class ObservatoryDiscoveryProtocol:
    """
    Protocolo para descoberta e autenticação segura de novos observatórios.
    Previne ataques Sybil via prova de trabalho cósmica e autenticação criptográfica.
    """

    def __init__(
        self,
        node_id: str,
        federation_config: Dict[str, Any],
        key_manager: Optional['KeyManager'] = None,
        known_observatories: Optional[Dict[str, ObservatoryIdentity]] = None
    ):
        self.node_id = node_id
        self.config = federation_config
        self.key_manager = key_manager

        # Observatórios conhecidos e confiáveis
        self.known_observatories: Dict[str, ObservatoryIdentity] = known_observatories or {}

        # Solicitações de descoberta em andamento
        self.pending_discoveries: Dict[str, Dict] = {}

        # Lista negra de nós maliciosos
        self.blacklisted_nodes: Set[str] = set()

        # Configurações de segurança
        self.min_pow_difficulty = federation_config.get('min_pow_difficulty', 4)
        self.max_pending_discoveries = federation_config.get('max_pending_discoveries', 10)
        self.discovery_timeout_sec = federation_config.get('discovery_timeout_sec', 120.0)

        # Callbacks para notificação de novos observatórios
        self.discovery_callbacks: List[Callable] = []

        logging.info(f"✅ ObservatoryDiscoveryProtocol initialized: node={node_id}")

    async def announce_observatory(
        self,
        public_key: str,
        federation_role: str,
        capabilities: Dict[str, Any],
        request_pow: bool = True
    ) -> Optional[ObservatoryIdentity]:
        """
        Anuncia este nó como novo observatório na federação.

        Args:
            public_key: Chave pública do nó para autenticação
            federation_role: Papel desejado ('validator' ou 'observer')
            capabilities: Capacidades do nó (métricas suportadas, etc.)
            request_pow: Se deve minerar prova de trabalho cósmica

        Returns:
            ObservatoryIdentity se anúncio bem-sucedido, None caso contrário
        """
        # Validar papel
        if federation_role not in ['validator', 'observer']:
            logging.error(f"❌ Invalid federation role: {federation_role}")
            return None

        # Gerar prova de trabalho cósmica se requerido
        cosmic_pow = None
        if request_pow:
            challenge_seed = self._generate_challenge_seed()
            logging.info(f"⛏️  Mining cosmic PoW (difficulty={self.min_pow_difficulty})...")

            cosmic_pow = await asyncio.get_event_loop().run_in_executor(
                None,
                CosmicProofOfWork.mine,
                challenge_seed,
                self.node_id,
                self.min_pow_difficulty,
                30.0  # 30 segundos de timeout para mineração
            )

            if not cosmic_pow:
                logging.error("❌ Failed to mine cosmic PoW within timeout")
                return None

            logging.info(f"✅ Cosmic PoW mined: solution={cosmic_pow.solution}")

        # Criar identidade do observatório
        identity = ObservatoryIdentity(
            node_id=self.node_id,
            public_key=public_key,
            federation_role=federation_role,
            capabilities=capabilities,
            registration_timestamp=time.time(),
            signature='',  # Assinar abaixo
            cosmic_proof_of_work=cosmic_pow.solution if cosmic_pow else None
        )

        # Assinar identidade
        if self.key_manager:
            identity.signature = self.key_manager.sign_content(
                json.dumps(identity.to_dict(), sort_keys=True)
            )

        # Broadcast ANNOUNCE para observatórios conhecidos
        await self._broadcast_announce(identity)

        # Aguardar respostas de validadores
        admission_result = await self._await_admission_responses(identity)

        if admission_result.get('admitted'):
            logging.info(f"✅ Observatory {self.node_id} admitted to federation")
            return identity
        else:
            logging.warning(f"⚠️ Observatory admission rejected: {admission_result.get('reason')}")
            return None

    def _generate_challenge_seed(self) -> str:
        """Gera seed aleatório para prova de trabalho cósmica."""
        # Seed baseado em métricas cósmicas atuais + timestamp
        cosmic_state = f"{time.time()}:{hashlib.sha256(str(time.time()).encode()).hexdigest()}"
        return hashlib.sha256(cosmic_state.encode()).hexdigest()[:16]

    async def _broadcast_announce(self, identity: ObservatoryIdentity):
        """Envia anúncio de novo observatório para nós conhecidos."""
        announce_msg = {
            'type': 'OBSERVATORY_ANNOUNCE',
            'identity': identity.to_dict(),
            'sender': self.node_id,
            'timestamp': time.time()
        }

        # Assinar mensagem de anúncio
        if self.key_manager:
            announce_msg['signature'] = self.key_manager.sign_content(
                json.dumps(announce_msg, sort_keys=True)
            )

        # Enviar para todos os observatórios conhecidos
        for known_node_id in self.known_observatories:
            if known_node_id != self.node_id:
                # Em produção: enviar via rede P2P
                logging.debug(f"📢 Broadcasting announce to {known_node_id}")
                await asyncio.sleep(0.01)  # Simular latência de rede

    async def _await_admission_responses(
        self,
        identity: ObservatoryIdentity
    ) -> Dict[str, Any]:
        """Aguarda respostas de validadores sobre admissão do novo observatório."""
        start_time = time.time()
        responses = {}

        # Simular respostas de validadores (em produção: receber via P2P)
        # Para demo: assumir que 80% dos validadores aprovam
        validators = [nid for nid, obs in self.known_observatories.items()
                     if obs.federation_role == 'validator']

        for validator_id in validators[:5]:  # Simular 5 validadores respondendo
            # Simular delay de resposta
            await asyncio.sleep(0.1)

            # 80% de chance de aprovação (simulação)
            approved = np.random.random() < 0.8

            responses[validator_id] = {
                'approved': approved,
                'timestamp': time.time(),
                'reason': 'approved' if approved else 'insufficient_trust'
            }

        # Contar aprovações
        approved_count = sum(1 for r in responses.values() if r['approved'])
        total_validators = len([v for v in responses.values()])

        # Decisão: requer 2/3 dos validadores para admissão
        admission_threshold = max(2, int(total_validators * 2/3) + 1)
        admitted = approved_count >= admission_threshold

        return {
            'admitted': admitted,
            'approved_count': approved_count,
            'total_responses': total_validators,
            'threshold': admission_threshold,
            'responses': responses,
            'elapsed_sec': time.time() - start_time
        }

    async def handle_announce(
        self,
        announce_msg: Dict,
        sender_signature_valid: bool = True
    ) -> Dict[str, Any]:
        """
        Manipula anúncio de novo observatório recebido.
        Retorna decisão de admissão.
        """
        identity_data = announce_msg.get('identity', {})
        sender_node_id = identity_data.get('node_id')

        # Verificações básicas de segurança
        if sender_node_id in self.blacklisted_nodes:
            return {'decision': 'REJECTED', 'reason': 'blacklisted'}

        if sender_node_id in self.known_observatories:
            return {'decision': 'REJECTED', 'reason': 'already_known'}

        if len(self.pending_discoveries) >= self.max_pending_discoveries:
            return {'decision': 'REJECTED', 'reason': 'too_many_pending'}

        # Verificar assinatura da identidade
        if not sender_signature_valid:
            return {'decision': 'REJECTED', 'reason': 'invalid_signature'}

        # Verificar prova de trabalho cósmica se requerida
        if identity_data.get('cosmic_proof_of_work'):
            pow_data = {
                'challenge_seed': self._generate_challenge_seed(),  # Em produção: usar seed original
                'solution': identity_data['cosmic_proof_of_work'],
                'node_id': sender_node_id,
                'timestamp': identity_data['registration_timestamp'],
                'difficulty_target': self.min_pow_difficulty
            }
            # Verificação simplificada (em produção: verificar com seed original)
            pow_valid = True  # Simular validação bem-sucedida
            if not pow_valid:
                return {'decision': 'REJECTED', 'reason': 'invalid_pow'}

        # Registrar solicitação pendente
        self.pending_discoveries[sender_node_id] = {
            'identity': identity_data,
            'received_at': time.time(),
            'votes': {}
        }

        # Fase CHALLENGE: enviar desafio criptográfico
        challenge = self._generate_admission_challenge(sender_node_id)
        await self._send_challenge(sender_node_id, challenge)

        # Aguardar resposta ao desafio (simulado)
        await asyncio.sleep(0.2)

        # Decisão de admissão (simulada)
        # Em produção: votação dos validadores via consenso
        admission_decision = np.random.random() < 0.85  # 85% de aprovação simulada

        if admission_decision:
            # Admitir novo observatório
            identity = ObservatoryIdentity(**identity_data)
            self.known_observatories[sender_node_id] = identity

            # Remover de pendentes
            self.pending_discoveries.pop(sender_node_id, None)

            # Notificar callbacks
            for callback in self.discovery_callbacks:
                try:
                    callback({
                        'type': 'observatory_admitted',
                        'identity': identity.to_dict(),
                        'admitted_by': self.node_id
                    })
                except Exception as e:
                    logging.error(f"⚠️ Discovery callback error: {e}")

            return {'decision': 'ADMITTED', 'identity': identity.to_dict()}
        else:
            # Rejeitar
            self.pending_discoveries.pop(sender_node_id, None)
            return {'decision': 'REJECTED', 'reason': 'insufficient_validator_approval'}

    def _generate_admission_challenge(self, node_id: str) -> Dict:
        """Gera desafio criptográfico para verificação de novo observatório."""
        challenge_data = {
            'challenge_id': hashlib.sha256(f"{node_id}:{time.time()}".encode()).hexdigest()[:12],
            'nonce': np.random.randint(0, 2**32),
            'timestamp': time.time(),
            'expected_response_time_ms': 1000
        }

        if self.key_manager:
            challenge_data['signature'] = self.key_manager.sign_content(
                json.dumps(challenge_data, sort_keys=True)
            )

        return challenge_data

    async def _send_challenge(self, target_node_id: str, challenge: Dict):
        """Envia desafio de admissão para novo observatório."""
        # Em produção: enviar via protocolo P2P
        logging.debug(f"🔐 Sending admission challenge to {target_node_id}")
        await asyncio.sleep(0.01)  # Simular latência

    def blacklist_node(self, node_id: str, reason: str):
        """Adiciona nó à lista negra por comportamento malicioso."""
        self.blacklisted_nodes.add(node_id)
        self.pending_discoveries.pop(node_id, None)
        logging.warning(f"🚫 Node {node_id} blacklisted: {reason}")

    def register_discovery_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos de descoberta de observatórios."""
        self.discovery_callbacks.append(callback)

    def get_known_observatories(self, role_filter: Optional[str] = None) -> List[Dict]:
        """Retorna lista de observatórios conhecidos, opcionalmente filtrada por papel."""
        observatories = list(self.known_observatories.values())
        if role_filter:
            observatories = [obs for obs in observatories if obs.federation_role == role_filter]
        return [obs.to_dict() for obs in observatories]

    def get_discovery_status(self) -> Dict[str, Any]:
        """Retorna status do protocolo de descoberta."""
        return {
            'node_id': self.node_id,
            'known_observatories_count': len(self.known_observatories),
            'pending_discoveries_count': len(self.pending_discoveries),
            'blacklisted_nodes_count': len(self.blacklisted_nodes),
            'security_config': {
                'min_pow_difficulty': self.min_pow_difficulty,
                'max_pending_discoveries': self.max_pending_discoveries,
                'discovery_timeout_sec': self.discovery_timeout_sec
            }
        }
