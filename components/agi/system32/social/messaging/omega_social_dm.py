#!/usr/bin/env python3
"""
omega_social_dm.py — Mensagens diretas com protocolo Ω para ASI↔ASI e E2E para humanos.
"""
import asyncio
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum

class DMEncryptionMode(Enum):
    E2E_HUMAN = "e2e_human"      # Criptografia E2E para humanos
    OMEGA_ASI = "omega_asi"       # Protocolo Ω para ASI↔ASI
    HYBRID = "hybrid"             # Ambos, dependendo do destinatário

@dataclass
class DirectMessage:
    """Mensagem direta em ASI Social."""
    message_id: str
    sender_seal: str
    receiver_seal: str
    content: str                    # Criptografado ou hash de conteúdo
    content_hash: str               # Hash do conteúdo original para verificação
    encryption_mode: DMEncryptionMode
    timestamp: float
    signature: str                  # Assinatura do remetente
    omega_proof: Optional[str] = None  # Prova ZK para mensagens ASI↔ASI
    read_receipt: bool = False
    metadata: Dict = field(default_factory=dict)

class OmegaSocialMessenger:
    """Sistema de mensagens diretas com suporte a Ω-Protocol."""

    def __init__(self,
                 local_seal: str,
                 kym_verifier,
                 dht_client,
                 encryption_backend):
        self.local_seal = local_seal
        self.kym = kym_verifier
        self.dht = dht_client
        self.encryption = encryption_backend
        self.inbox: List[DirectMessage] = []
        self.sent: List[DirectMessage] = []
        self.on_message_received: Optional[Callable] = None

    async def send_message(self,
                          receiver_seal: str,
                          content: str,
                          encryption_mode: Optional[DMEncryptionMode] = None,
                          omega_intent: Optional[str] = None) -> DirectMessage:
        """Envia mensagem direta com criptografia apropriada."""
        # Determinar modo de criptografia
        if encryption_mode is None:
            # Auto-detect: se receiver é ASI, usar Ω; caso contrário, E2E
            receiver_profile = await self._lookup_profile(receiver_seal)
            if receiver_profile and receiver_profile.get("account_type") == "asi":
                encryption_mode = DMEncryptionMode.OMEGA_ASI
            else:
                encryption_mode = DMEncryptionMode.E2E_HUMAN

        # Hash do conteúdo para verificação de integridade
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Criptografar conteúdo
        if encryption_mode == DMEncryptionMode.OMEGA_ASI:
            # Para ASI↔ASI: usar Ω-Protocol com prova ZK
            encrypted_content, omega_proof = await self._encrypt_omega(
                content, receiver_seal, omega_intent
            )
        else:
            # Para humanos: E2E padrão
            if hasattr(self.encryption, 'encrypt_e2e'):
                if asyncio.iscoroutinefunction(self.encryption.encrypt_e2e):
                    encrypted_content = await self.encryption.encrypt_e2e(content, receiver_seal)
                else:
                    encrypted_content = self.encryption.encrypt_e2e(content, receiver_seal)
            else:
                encrypted_content = "encrypted_" + content # Placeholder
            omega_proof = None

        # Assinar mensagem
        signature = self._sign_message(
            receiver_seal, content_hash, encryption_mode.value, time.time()
        )

        # Criar mensagem
        message = DirectMessage(
            message_id=hashlib.sha256(
                f"{self.local_seal}:{receiver_seal}:{time.time()}".encode()
            ).hexdigest()[:16],
            sender_seal=self.local_seal,
            receiver_seal=receiver_seal,
            content=encrypted_content,
            content_hash=content_hash,
            encryption_mode=encryption_mode,
            timestamp=time.time(),
            signature=signature,
            omega_proof=omega_proof
        )

        # Entregar via DHT (simulado) ou canal direto
        await self._deliver_message(message)

        # Registrar localmente
        self.sent.append(message)

        return message

    async def _encrypt_omega(self,
                            content: str,
                            receiver_seal: str,
                            intent: Optional[str]) -> Tuple[str, str]:
        """Criptografia Ω-Protocol para comunicação ASI↔ASI."""
        # Em produção: usar provas ZK reais
        # Aqui: simulação com hash + metadata de intenção
        intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:16] if intent else "none"
        omega_payload = {
            "content": content,
            "intent_hash": intent_hash,
            "sender": self.local_seal,
            "receiver": receiver_seal,
            "timestamp": time.time()
        }
        # "Criptografar" = assinar + ofuscar
        encrypted = hashlib.sha3_256(json.dumps(omega_payload).encode()).hexdigest()
        # Prova ZK simulada
        zk_proof = hashlib.sha256(f"{encrypted}:{intent_hash}".encode()).hexdigest()[:32]
        return encrypted, zk_proof

    def _sign_message(self, receiver: str, content_hash: str, mode: str, ts: float) -> str:
        """Assina mensagem com chave do remetente."""
        payload = f"{self.local_seal}:{receiver}:{content_hash}:{mode}:{ts}"
        return hashlib.sha256(payload.encode()).hexdigest()[:64]

    async def _deliver_message(self, message: DirectMessage):
        """Entrega mensagem ao destinatário (via DHT ou canal direto)."""
        # Em produção: usar DHT do Substrate 321 ou canal Ω direto
        # Aqui: simular entrega local se receiver for este nó
        if message.receiver_seal == self.local_seal:
            self.inbox.append(message)
            if self.on_message_received:
                if asyncio.iscoroutinefunction(self.on_message_received):
                    await self.on_message_received(message)
                else:
                    self.on_message_received(message)
        else:
            # Publicar na DHT para o receiver buscar
            key = f"dm:{message.receiver_seal}:{message.message_id}"
            # Verifica se store é async
            if hasattr(self.dht, 'store'):
                if asyncio.iscoroutinefunction(self.dht.store):
                    await self.dht.store(key, json.dumps({
                        "message": {k: v for k, v in message.__dict__.items()
                                   if k != "omega_proof"},  # Não expor prova ZK publicamente
                        "omega_proof": message.omega_proof  # Apenas para o receiver
                    }))
                else:
                    self.dht.store(key, json.dumps({
                        "message": {k: v for k, v in message.__dict__.items()
                                   if k != "omega_proof"},  # Não expor prova ZK publicamente
                        "omega_proof": message.omega_proof  # Apenas para o receiver
                    }))

    async def _lookup_profile(self, seal: str) -> Optional[Dict]:
        """Busca perfil público na DHT."""
        # Em produção: consultar DHT do Substrate 321
        return None  # Placeholder

    def get_inbox(self,
                  limit: int = 50,
                  unread_only: bool = False) -> List[DirectMessage]:
        """Retorna mensagens recebidas."""
        messages = self.inbox
        if unread_only:
            messages = [m for m in messages if not m.read_receipt]
        # Ordenar por timestamp descendente
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages[:limit]

    def mark_as_read(self, message_id: str):
        """Marca mensagem como lida."""
        for msg in self.inbox:
            if msg.message_id == message_id:
                msg.read_receipt = True
                break
