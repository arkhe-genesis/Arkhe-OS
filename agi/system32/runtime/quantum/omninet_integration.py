# omninet_integration.py — Integração RCP v2.0 com OmniNet Protocol Stack
# ARKHE OS — Substrate 316: Quantum-Classical Hybrid Networking

import asyncio
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum

# Imports locais
from rcp_v2_engine import RetrocausalChannel8Bit, QHTTPPacket, QHTTPRetrocausalTransport


class OmniNetMessageType(Enum):
    """Tipos de mensagem no protocolo OmniNet."""
    RCP_TRANSMIT = "rcp_transmit"           # Transmissão via canal retrógrado
    RCP_RECEIVE = "rcp_receive"             # Recebimento via canal retrógrado
    COHERENCE_SYNC = "coherence_sync"       # Sincronização de campo de coerência
    KAPPA_UPDATE = "kappa_update"           # Atualização de acoplamento cósmico
    INTENT_BROADCAST = "intent_broadcast"   # Difusão de intenção soberana
    ORACLE_QUERY = "oracle_query"           # Consulta ao oráculo Omni
    ORACLE_RESPONSE = "oracle_response"     # Resposta do oráculo Omni


@dataclass
class OmniNetMessage:
    """Mensagem do protocolo OmniNet com suporte a transporte híbrido."""
    msg_id: str
    msg_type: OmniNetMessageType
    src_node: str
    dst_node: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    # Metadados de transporte
    transport_preference: str = "hybrid"  # "retrocausal", "classical", "hybrid"
    coherence_requirement: float = 0.8    # Coerência mínima para transmissão
    priority: float = 1.0                 # Prioridade da mensagem (0.0-1.0)

    # Assinatura e verificação
    signature: Optional[str] = None
    signature_algorithm: str = "sha256"

    def compute_signature(self, secret_key: str) -> str:
        """Computar assinatura criptográfica da mensagem."""
        data = f"{self.msg_id}:{self.msg_type.value}:{self.src_node}:{self.dst_node}:{json.dumps(self.payload, sort_keys=True)}:{self.timestamp}"
        return hashlib.sha256(f"{data}:{secret_key}".encode()).hexdigest()

    def verify_signature(self, secret_key: str) -> bool:
        """Verificar assinatura criptográfica da mensagem."""
        if not self.signature:
            return False
        expected = self.compute_signature(secret_key)
        return self.signature == expected

    def to_dict(self) -> Dict:
        """Converter mensagem para dicionário (para serialização)."""
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type.value,
            "src_node": self.src_node,
            "dst_node": self.dst_node,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "transport_preference": self.transport_preference,
            "coherence_requirement": self.coherence_requirement,
            "priority": self.priority,
            "signature": self.signature,
            "signature_algorithm": self.signature_algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'OmniNetMessage':
        """Criar mensagem a partir de dicionário."""
        return cls(
            msg_id=data["msg_id"],
            msg_type=OmniNetMessageType(data["msg_type"]),
            src_node=data["src_node"],
            dst_node=data["dst_node"],
            payload=data["payload"],
            timestamp=data.get("timestamp", time.time()),
            transport_preference=data.get("transport_preference", "hybrid"),
            coherence_requirement=data.get("coherence_requirement", 0.8),
            priority=data.get("priority", 1.0),
            signature=data.get("signature"),
            signature_algorithm=data.get("signature_algorithm", "sha256"),
        )


class OmniNetIntegrationLayer:
    """
    Camada de integração entre RCP v2.0 e OmniNet Protocol Stack.
    Gerencia transporte híbrido quântico-clássico com fallback automático.
    """

    def __init__(self, node_id: str, rcp_channel: RetrocausalChannel8Bit,
                 secret_key: str, coherence_threshold: float = 0.8):
        self.node_id = node_id
        self.rcp_channel = rcp_channel
        self.rcp_transport = QHTTPRetrocausalTransport(node_id, rcp_channel)
        self.secret_key = secret_key
        self.coherence_threshold = coherence_threshold

        # Estado da conexão
        self.connected_peers: Dict[str, Dict] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}

        # Métricas
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "retrocausal_transmissions": 0,
            "classical_fallbacks": 0,
            "coherence_failures": 0,
            "avg_latency_ms": 0.0,
        }

    async def connect_to_peer(self, peer_id: str, endpoint: str,
                             initial_coherence: float = 0.7) -> bool:
        """Estabelecer conexão com peer na rede OmniNet."""
        self.connected_peers[peer_id] = {
            "endpoint": endpoint,
            "coherence": initial_coherence,
            "last_heartbeat": time.time(),
            "transport_mode": "hybrid",
        }

        # Enviar handshake inicial
        handshake = OmniNetMessage(
            msg_id=f"handshake_{self.node_id}_{int(time.time()*1e6)}",
            msg_type=OmniNetMessageType.COHERENCE_SYNC,
            src_node=self.node_id,
            dst_node=peer_id,
            payload={"version": "316.0", "capabilities": ["rcp_v2", "omni_oracle"]},
            coherence_requirement=0.5,  # Baixa exigência para handshake
        )
        handshake.signature = handshake.compute_signature(self.secret_key)

        success = await self._send_message(handshake, peer_id)
        if success:
            print(f"🔗 Conectado a {peer_id} (coerência inicial: {initial_coherence:.2f})")
        return success

    async def send_message(self, message: OmniNetMessage,
                          peer_id: str) -> bool:
        return await self._send_message(message, peer_id)

    async def _send_message(self, message: OmniNetMessage,
                          peer_id: str) -> bool:
        """Enviar mensagem via transporte híbrido com fallback automático."""
        # Assinar mensagem
        message.signature = message.compute_signature(self.secret_key)

        # Verificar coerência do peer
        peer_info = self.connected_peers.get(peer_id)
        if not peer_info:
            print(f"❌ Peer {peer_id} não conectado")
            return False

        # Decidir modo de transporte
        transport_mode = self._select_transport_mode(
            message, peer_info["coherence"], peer_info["transport_mode"]
        )

        # Enviar via modo selecionado
        start_time = time.time()
        success = False

        if transport_mode == "retrocausal" and message.transport_preference != "classical":
            success = await self._send_via_retrocausal(message, peer_id)
            if success:
                self.stats["retrocausal_transmissions"] += 1

        if not success and transport_mode != "retrocausal":
            # Fallback para transporte clássico
            success = await self._send_via_classical(message, peer_id)
            if success and transport_mode != "classical":
                self.stats["classical_fallbacks"] += 1

        # Atualizar métricas
        if success:
            latency = (time.time() - start_time) * 1000
            self.stats["avg_latency_ms"] = (
                self.stats["avg_latency_ms"] * 0.9 + latency * 0.1
            )
            self.stats["messages_sent"] += 1
            print(f"✅ Mensagem enviada via {transport_mode} (latência: {latency:.1f}ms)")
        else:
            self.stats["coherence_failures"] += 1
            print(f"❌ Falha ao enviar mensagem para {peer_id}")

        return success

    async def _send_via_retrocausal(self, message: OmniNetMessage,
                                   peer_id: str) -> bool:
        """Enviar mensagem via canal retrógrado RCP v2.0."""
        # Serializar mensagem para bytes
        msg_bytes = json.dumps(message.to_dict()).encode('utf-8')

        # Transmitir byte a byte via RCP
        for byte_val in msg_bytes:
            packet = self.rcp_transport.send_retrocausal_byte(
                peer_id, byte_val,
                t_weak=0.5, t_post=1.5, n_shots=50
            )

            # Verificar coerência do pacote
            if not packet.coherence_verified:
                print(f"⚠️ Pacote não verificado: {packet.retrocausal_signature}")
                return False

        return True

    async def _send_via_classical(self, message: OmniNetMessage,
                                 peer_id: str) -> bool:
        """Enviar mensagem via transporte clássico (fallback)."""
        # Em produção: usar TCP/TLS, gRPC, ou outro protocolo clássico
        # Aqui: simular envio clássico bem-sucedido
        peer_info = self.connected_peers.get(peer_id)
        if not peer_info:
            return False

        # Simular latência de rede clássica
        await asyncio.sleep(0.05)  # 50ms simulados
        return True

    def _select_transport_mode(self, message: OmniNetMessage,
                              peer_coherence: float,
                              current_mode: str) -> str:
        """Selecionar modo de transporte baseado em coerência e requisitos."""
        # Priorizar transporte retrógrado se:
        # 1. Coerência do peer é alta o suficiente
        # 2. Mensagem requer alta coerência
        # 3. Preferência de transporte não é clássica
        if (peer_coherence >= self.coherence_threshold and
            message.coherence_requirement >= self.coherence_threshold and
            message.transport_preference != "classical"):
            return "retrocausal"

        # Usar transporte clássico como fallback ou se preferido
        return "classical"

    async def receive_loop(self):
        """Loop principal de recebimento de mensagens."""
        print(f"📡 {self.node_id} iniciando loop de recebimento...")

        while True:
            try:
                # Simular recebimento de mensagem (em produção: ler de socket/fila)
                await asyncio.sleep(0.1)  # Polling interval

                # Processar mensagens na fila
                while not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self._handle_received_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Erro no loop de recebimento: {e}")
                await asyncio.sleep(1.0)  # Backoff em caso de erro

    async def _handle_received_message(self, message: OmniNetMessage):
        """Processar mensagem recebida."""
        # Verificar assinatura
        if not message.verify_signature(self.secret_key):
            print(f"⚠️ Assinatura inválida de {message.src_node}")
            return

        # Atualizar coerência do peer se for mensagem de sincronização
        if message.msg_type == OmniNetMessageType.COHERENCE_SYNC:
            peer_coherence = message.payload.get("coherence", 0.7)
            if message.src_node in self.connected_peers:
                self.connected_peers[message.src_node]["coherence"] = peer_coherence
                self.connected_peers[message.src_node]["last_heartbeat"] = time.time()

        # Despachar para handler registrado
        handler = self.response_handlers.get(message.msg_type.value)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                print(f"❌ Erro ao processar mensagem {message.msg_type.value}: {e}")

        self.stats["messages_received"] += 1

    def register_handler(self, msg_type: OmniNetMessageType,
                        handler: Callable[[OmniNetMessage], Any]):
        """Registrar handler para tipo de mensagem."""
        self.response_handlers[msg_type.value] = handler

    def get_stats(self) -> Dict:
        """Obter estatísticas da camada de integração."""
        return {
            **self.stats,
            "connected_peers": len(self.connected_peers),
            "pending_messages": self.message_queue.qsize(),
        }

    async def shutdown(self):
        """Encerrar camada de integração gracefulmente."""
        print(f"🔌 {self.node_id} encerrando conexão OmniNet...")
        # Limpar recursos, fechar conexões, etc.
        self.connected_peers.clear()
        while not self.message_queue.empty():
            self.message_queue.get_nowait()
