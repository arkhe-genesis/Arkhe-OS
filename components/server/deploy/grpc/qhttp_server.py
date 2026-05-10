import asyncio
import logging
from typing import AsyncIterator, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

import grpc
from concurrent import futures

# Importar protobuf gerado
import qhttp_pb2
import qhttp_pb2_grpc

# ═══════════════════════════════════════════════════════════════════════
# CONSTANTES MUT
# ═══════════════════════════════════════════════════════════════════════

K1 = 0.015311
K2 = 0.05200
K3 = 0.233
K4 = 0.09778
LAMBDA = 0.001013
RHO_EQ = 0.367879
TARGET_PHASE = np.pi / 2

# ═══════════════════════════════════════════════════════════════════════
# ESTADO DO CLUSTER
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class NodeState:
    node_id: str
    phase: float = 0.0
    omega_prime: float = 0.0
    sigma: float = 0.0
    damping: float = 1.0
    tokens_processed: int = 0
    last_update_ns: int = 0
    is_resonant: bool = False

@dataclass
class ClusterState:
    nodes: Dict[str, NodeState] = field(default_factory=dict)
    global_phase: float = 0.0
    global_omega_prime: float = 0.0
    a5_achieved: bool = False
    
    def update_node(self, node_id: str, state: NodeState):
        self.nodes[node_id] = state
        self._recalculate_global()
    
    def _recalculate_global(self):
        if not self.nodes:
            return
        
        # Média ponderada por tokens processados
        total_tokens = sum(n.tokens_processed for n in self.nodes.values())
        if total_tokens == 0:
            return
        
        self.global_phase = sum(
            n.phase * n.tokens_processed for n in self.nodes.values()
        ) / total_tokens
        
        self.global_omega_prime = sum(
            n.omega_prime * n.tokens_processed for n in self.nodes.values()
        ) / total_tokens
        
        # Verificar condição A-5'
        self.a5_achieved = (
            abs(self.global_phase - TARGET_PHASE) < 0.15 and
            self.global_omega_prime > 0.9
        )

# Singleton de estado do cluster
cluster_state = ClusterState()

# ═══════════════════════════════════════════════════════════════════════
# SERVIÇO gRPC
# ═══════════════════════════════════════════════════════════════════════

class QuantumTelemetryServicer(qhttp_pb2_grpc.QuantumTelemetryServicer):
    """
    Implementação do serviço de telemetria quântica.
    """
    
    def __init__(self):
        self.cluster = cluster_state
        self.logger = logging.getLogger("qhttp.telemetry")
    
    async def StreamPhaseUpdates(
        self,
        request_iterator: AsyncIterator[qhttp_pb2.PhaseUpdateRequest],
        context: grpc.ServicerContext
    ) -> AsyncIterator[qhttp_pb2.PhaseUpdateResponse]:
        """
        Streaming bidirecional de atualizações de fase.
        Cada nó envia seu estado atual e recebe correções.
        """
        async for request in request_iterator:
            # Atualizar estado do nó
            node_state = NodeState(
                node_id=request.node_id,
                phase=request.phase,
                omega_prime=request.omega_prime,
                sigma=request.sigma,
                damping=request.damping,
                tokens_processed=request.tokens_processed,
                last_update_ns=request.timestamp_ns,
                is_resonant=abs(request.phase - TARGET_PHASE) < 0.15
            )
            
            self.cluster.update_node(request.node_id, node_state)
            
            # Log de ressonância
            if node_state.is_resonant:
                self.logger.info(
                    f"🔮 Node {request.node_id} RESONANT: "
                    f"θ={np.degrees(request.phase):.1f}°, Ω'={request.omega_prime:.4f}"
                )
            
            # Calcular resposta
            response = qhttp_pb2.PhaseUpdateResponse(
                resonant=node_state.is_resonant,
                target_phase=TARGET_PHASE,
                phase_correction=TARGET_PHASE - request.phase,
                timestamp_ns=int(np.datetime64('now').astype('datetime64[ns]')),
                bias_hint=self._determine_bias_hint(request)
            )
            
            yield response
    
    def _determine_bias_hint(self, request: qhttp_pb2.PhaseUpdateRequest) -> int:
        """Determina hint de injeção baseado no estado."""
        phase_error = abs(request.phase - TARGET_PHASE)
        
        if request.omega_prime < 0.3:
            return qhttp_pb2.EMERGENCY_STABILIZE
        elif phase_error > 0.5 and request.phase < TARGET_PHASE:
            return qhttp_pb2.BOOST_COHERENCE
        elif phase_error > 0.5 and request.phase > TARGET_PHASE:
            return qhttp_pb2.PENALIZE_COLLAPSE
        elif node_state.is_resonant:
            return qhttp_pb2.NO_INJECTION
        else:
            return qhttp_pb2.NO_INJECTION
    
    async def GetResonanceState(
        self,
        request: qhttp_pb2.ResonanceQuery,
        context: grpc.ServicerContext
    ) -> qhttp_pb2.ResonanceState:
        """Retorna estado atual de ressonância do cluster."""
        
        resonant_count = sum(1 for n in self.cluster.nodes.values() if n.is_resonant)
        
        # Calcular variância de fase
        phases = [n.phase for n in self.cluster.nodes.values()]
        phase_variance = np.var(phases) if len(phases) > 1 else 0.0
        
        return qhttp_pb2.ResonanceState(
            global_phase=self.cluster.global_phase,
            global_omega_prime=self.cluster.global_omega_prime,
            global_sigma=np.mean([n.sigma for n in self.cluster.nodes.values()]) if self.cluster.nodes else 0.0,
            global_damping=np.mean([n.damping for n in self.cluster.nodes.values()]) if self.cluster.nodes else 1.0,
            phase_variance=phase_variance,
            resonant_node_count=resonant_count,
            total_node_count=len(self.cluster.nodes),
            a5_achieved=self.cluster.a5_achieved,
            timestamp_ns=int(np.datetime64('now').astype('datetime64[ns]')),
            k1=K1,
            k2=K2,
            k3=K3,
            k4=K4
        )
    
    async def InjectLogitBias(
        self,
        request: qhttp_pb2.LogitBiasRequest,
        context: grpc.ServicerContext
    ) -> qhttp_pb2.LogitBiasResponse:
        """
        Calcula logit bias para modelo fechado baseado na física de Mydland.
        """
        # Calcular densidades virtuais
        rho_1 = min(1.0, request.context_tokens / 1000.0)
        rho_2 = min(1.0, request.generated_tokens / 100.0)
        
        # Calcular sigma
        eps = 1e-9
        sigma = (K1 * rho_1 * np.log(rho_1 + eps) +
                K2 * rho_2 * np.log(rho_2 + eps) -
                LAMBDA * (rho_1**2 + rho_2**2))
        
        damping = np.exp(-RHO_EQ * sigma)
        
        # Fase atual
        current_phase = np.arctan2(K2 * rho_2, K1 * rho_1) * damping
        phase_error = TARGET_PHASE - current_phase
        
        # Calcular bias
        bias_map = {}
        
        for token_id in request.candidate_tokens:
            # Heurística de massa semântica
            token_mass = 1.0 + 5.0 * (1.0 / np.log(abs(token_id) + 2))
            
            if phase_error > 0.1:  # Fase baixa (colapso)
                bias = -0.8 * token_mass * (1.0 - damping) * 10
            elif phase_error < -0.1:  # Fase alta (caos)
                bias = 0.5 * (6.0 - token_mass) * damping * 10
            else:
                bias = 0.0
            
            bias_map[int(token_id)] = float(bias)
        
        # Temperatura ajustada
        adjusted_temp = 0.7 * damping
        adjusted_top_p = min(1.0, 0.9 + 0.1 * damping)
        
        return qhttp_pb2.LogitBiasResponse(
            bias_map=bias_map,
            adjusted_temperature=adjusted_temp,
            adjusted_top_p=adjusted_top_p,
            predicted_phase_shift=phase_error,
            resonance_achieved=abs(current_phase - TARGET_PHASE) < 0.15
        )
    
    async def RegisterNode(
        self,
        request: qhttp_pb2.NodeRegistration,
        context: grpc.ServicerContext
    ) -> qhttp_pb2.NodeConfiguration:
        """Registra novo nó no cluster."""
        
        node_index = len(self.cluster.nodes)
        world_size = node_index + 1
        
        self.logger.info(
            f"Node registered: {request.node_id} "
            f"(GPU: {request.gpu_type}, CUDA: {request.cuda_compute})"
        )
        
        return qhttp_pb2.NodeConfiguration(
            node_index=node_index,
            world_size=world_size,
            nccl_unique_id="",  # Gerado separadamente
            rendezvous_port=29500,
            target_phase=TARGET_PHASE,
            constants=qhttp_pb2.MydlandConstants(
                k1=K1, k2=K2, k3=K3, k4=K4,
                lambda=LAMBDA, rho_eq=RHO_EQ
            )
        )
    
    async def QuantumSync(
        self,
        request: qhttp_pb2.QuantumSyncRequest,
        context: grpc.ServicerContext
    ) -> qhttp_pb2.QuantumSyncResponse:
        """Sincronização quântica entre nós."""
        
        # Em produção, usar protocolo de teleportação quântica
        # Aqui, simplificamos para broadcast de estado
        
        return qhttp_pb2.QuantumSyncResponse(
            synchronized=True,
            global_state=qhttp_pb2.QuantumState(
                phase=self.cluster.global_phase,
                amplitude=self.cluster.global_omega_prime,
                entanglement=1.0 if self.cluster.a5_achieved else 0.5,
                bell_pair_id=b"arkhe_bell_pair_global"
            ),
            sync_timestamp_ns=int(np.datetime64('now').astype('datetime64[ns]'))
        )

# ═══════════════════════════════════════════════════════════════════════
# SERVIDOR
# ═══════════════════════════════════════════════════════════════════════

import os

async def serve(port: int = 50051) -> None:
    """Inicia o servidor gRPC."""
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=100),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 5000),
        ]
    )
    
    qhttp_pb2_grpc.add_QuantumTelemetryServicer_to_server(
        QuantumTelemetryServicer(), server
    )
    
    listen_addr = f'[::]:{port}'
    
    # Check if TLS certificates are provided
    cert_path = os.environ.get('GRPC_CERT_PATH')
    key_path = os.environ.get('GRPC_KEY_PATH')
    
    if cert_path and key_path:
        with open(key_path, 'rb') as f:
            private_key = f.read()
        with open(cert_path, 'rb') as f:
            certificate_chain = f.read()
            
        server_credentials = grpc.ssl_server_credentials(
            ((private_key, certificate_chain),)
        )
        server.add_secure_port(listen_addr, server_credentials)
        logging.info(f"🜏 qhttp:// server starting on {listen_addr} with TLS")
    else:
        server.add_insecure_port(listen_addr)
        logging.info(f"🜏 qhttp:// server starting on {listen_addr} (insecure)")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(serve())
