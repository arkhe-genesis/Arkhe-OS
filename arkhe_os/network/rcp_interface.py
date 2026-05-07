import asyncio
import numpy as np
import time
from typing import Dict, List, Optional, Callable, Awaitable, Union
from collections import defaultdict

from arkhe_os.network.rcp_message import RCPMessage, RCPMessageType, RetroPhase
from arkhe_os._integrity import IntegrityError

class SecurityError(Exception):
    pass

class RCPConnection:
    """Dummy RCPConnection para o RCPInterface."""
    def __init__(self, local_node, remote_node, endpoint, hardware_config, qkd_setup):
        self.local_node = local_node
        self.remote_node = remote_node
        self.endpoint = endpoint
        self.hardware_config = hardware_config
        self.qkd_setup = qkd_setup

    async def establish(self):
        pass

    async def exchange_qkd_keys(self) -> bytes:
        return b"dummy_qkd_key_123"

    async def schedule_transmission(self, msg: RCPMessage, priority: float, decoherence_window: float):
        pass


class RCPInterface:
    """
    Interface de alto nível para comunicação retrocausal em rede federada.

    Responsabilidades:
    • Gerenciar conexões RCP com outros nós (quântico + clássico fallback)
    • Codificar/decodificar mensagens com weak values e gradientes
    • Agendar transmissões considerando janelas de decoerência
    • Autenticar mensagens via QKD
    • Bufferizar e retransmitir em caso de falha quântica
    """

    def __init__(self, node_id: str, hardware_config: Dict[str, any]):
        self.node_id = node_id
        self.hardware_config = hardware_config  # Config do hardware de cristal de tempo
        self.connections: Dict[str, 'RCPConnection'] = {}  # node_id → conexão
        self.message_handlers: Dict[RCPMessageType, List[Callable]] = defaultdict(list)
        self.qkd_keys: Dict[str, bytes] = {}  # node_id → chave QKD compartilhada
        self.decoherence_window = hardware_config.get("decoherence_ratio", 0.077)

    async def connect_to_node(self, target_node: str, endpoint: str, qkd_setup: Dict[str, any]):
        """Estabelece conexão RCP com outro nó da rede."""
        conn = RCPConnection(
            local_node=self.node_id,
            remote_node=target_node,
            endpoint=endpoint,
            hardware_config=self.hardware_config,
            qkd_setup=qkd_setup
        )
        await conn.establish()
        self.connections[target_node] = conn
        self.qkd_keys[target_node] = await conn.exchange_qkd_keys()

    def register_handler(self, msg_type: RCPMessageType, handler: Callable[[RCPMessage], Awaitable[None]]):
        """Registra handler assíncrono para tipo de mensagem."""
        self.message_handlers[msg_type].append(handler)

    async def send_retrocausal(self, target_nodes: Union[str, List[str]],
                              payload: Dict[str, any],
                              msg_type: RCPMessageType = RCPMessageType.WEAK_VALUE,
                              phase: RetroPhase = RetroPhase.PHI_0,
                              priority: float = 1.0,
                              temporal_scope: Optional[Dict[str, float]] = None):
        """
        Envia mensagem via canal retrocausal para nós alvo.

        Args:
            target_nodes: ID único ou lista de IDs de nós destino
            payload: Dicionário com dados da mensagem (será tipado conforme msg_type)
            msg_type: Tipo de mensagem RCP
            phase: Fase de controle do canal (determina direção do fluxo de intenção)
            priority: Prioridade para agendamento (maior = mais urgente)
            temporal_scope: Janela temporal para inferência atemporal {"t_min": ..., "t_max": ...}
        """
        targets = [target_nodes] if isinstance(target_nodes, str) else target_nodes

        for target in targets:
            if target not in self.connections:
                # Fallback: enviar via canal clássico
                await self._send_classical_fallback(target, payload, msg_type)
                continue

            conn = self.connections[target]
            qkd_key = self.qkd_keys.get(target)

            # Criar mensagem RCP
            msg = RCPMessage(
                msg_id=f"{self.node_id}_{int(time.time()*1e6)}_{np.random.randint(10000)}",
                msg_type=msg_type,
                sender_node=self.node_id,
                timestamp=time.time(),
                payload=payload,
                intended_recipients=[target],
                temporal_scope=temporal_scope,
                phase=phase,
                priority=priority
            )

            # Assinar com chave quântica se disponível
            if qkd_key:
                msg = msg.sign_quantum(qkd_key)
            else:
                # Fallback: hash clássico
                msg.classical_hash = msg.compute_classical_hash()

            # Agendar transmissão considerando janela de decoerência
            await conn.schedule_transmission(msg, priority=priority, decoherence_window=self.decoherence_window)

    async def broadcast_classical(self, msg_type: str, proposal: any):
        pass

    async def broadcast_retrocausal(self, payload: Dict[str, any], phase: RetroPhase):
        pass

    def get_shared_nonce(self, node_id: str) -> bytes:
        return b"dummy_nonce"

    async def _send_classical_fallback(self, target: str, payload: Dict, msg_type: RCPMessageType):
        """Envia mensagem via canal clássico quando RCP não está disponível."""
        # Implementação: gRPC/HTTP com criptografia clássica
        # Aqui: placeholder para demonstração
        print(f"[FALLBACK] Sending {msg_type.value} to {target} via classical channel")

    async def _dispatch_message(self, msg: RCPMessage):
        """Despacha mensagem recebida para handlers registrados."""
        # Verificar integridade
        if msg.quantum_signature:
            qkd_key = self.qkd_keys.get(msg.sender_node)
            if qkd_key and not msg.verify_quantum(qkd_key):
                raise SecurityError(f"Invalid quantum signature from {msg.sender_node}")
        elif msg.classical_hash:
            expected_hash = msg.compute_classical_hash()
            if msg.classical_hash != expected_hash:
                raise IntegrityError(f"Classical hash mismatch from {msg.sender_node}")

        # Despachar para handlers
        for handler in self.message_handlers[msg.msg_type]:
            try:
                await handler(msg)
            except Exception as e:
                print(f"Error in handler for {msg.msg_type}: {e}")
                # Log para auditoria
