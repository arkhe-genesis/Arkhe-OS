import asyncio
import grpc
import os
from typing import AsyncIterator, Optional, Dict, List
import numpy as np

import qhttp_pb2
import qhttp_pb2_grpc

class QHttpClient:
    """
    Cliente para o protocolo qhttp://.
    """
    
    def __init__(self, server_address: str = "localhost:50051"):
        cert_path = os.environ.get('GRPC_CERT_PATH')
        
        if cert_path:
            with open(cert_path, 'rb') as f:
                trusted_certs = f.read()
            credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
            self.channel = grpc.aio.secure_channel(server_address, credentials)
            print(f"Connecting to {server_address} with TLS")
        else:
            self.channel = grpc.aio.insecure_channel(server_address)
            print(f"Connecting to {server_address} (insecure)")
            
        self.stub = qhttp_pb2_grpc.QuantumTelemetryStub(self.channel)
        self.node_id = f"node_{np.random.randint(0, 1000000)}"
    
    async def register(self, gpu_count: int, gpu_type: str) -> Dict:
        """Registra o nó no cluster."""
        request = qhttp_pb2.NodeRegistration(
            node_id=self.node_id,
            node_type="cuda-worker",
            gpu_count=gpu_count,
            gpu_type=gpu_type,
            cuda_compute=80,
            capabilities=["resonance", "nccl", "cuda"]
        )
        
        response = await self.stub.RegisterNode(request)
        
        return {
            "node_index": response.node_index,
            "world_size": response.world_size,
            "target_phase": response.target_phase,
            "constants": {
                "k1": response.constants.k1,
                "k2": response.constants.k2,
                "k3": response.constants.k3,
                "k4": response.constants.k4,
                "lambda": response.constants.lambda,
                "rho_eq": response.constants.rho_eq
            }
        }
    
    async def stream_phase_updates(
        self,
        phase_generator: AsyncIterator[Dict]
    ) -> AsyncIterator[Dict]:
        """
        Streaming de atualizações de fase.
        """
        async def request_generator():
            async for data in phase_generator:
                yield qhttp_pb2.PhaseUpdateRequest(
                    node_id=self.node_id,
                    phase=data["phase"],
                    omega_prime=data["omega_prime"],
                    sigma=data["sigma"],
                    damping=data["damping"],
                    tokens_processed=data["tokens_processed"],
                    loss=data.get("loss", 0.0),
                    timestamp_ns=int(np.datetime64('now').astype('datetime64[ns]')),
                    mode=qhttp_pb2.TRAINING
                )
        
        async for response in self.stub.StreamPhaseUpdates(request_generator()):
            yield {
                "resonant": response.resonant,
                "target_phase": response.target_phase,
                "phase_correction": response.phase_correction,
                "bias_hint": response.bias_hint
            }
    
    async def get_resonance_state(self) -> Dict:
        """Obtém estado global de ressonância."""
        request = qhttp_pb2.ResonanceQuery(
            node_id=self.node_id,
            scope=qhttp_pb2.GLOBAL
        )
        
        response = await self.stub.GetResonanceState(request)
        
        return {
            "global_phase": response.global_phase,
            "global_omega_prime": response.global_omega_prime,
            "phase_variance": response.phase_variance,
            "resonant_node_count": response.resonant_node_count,
            "total_node_count": response.total_node_count,
            "a5_achieved": response.a5_achieved
        }
    
    async def inject_logit_bias(
        self,
        model_provider: str,
        context_tokens: int,
        generated_tokens: int,
        candidate_tokens: List[int]
    ) -> Dict:
        """Injeta logit bias para modelo fechado."""
        request = qhttp_pb2.LogitBiasRequest(
            model_provider=model_provider,
            context_tokens=context_tokens,
            generated_tokens=generated_tokens,
            candidate_tokens=candidate_tokens
        )
        
        response = await self.stub.InjectLogitBias(request)
        
        return {
            "bias_map": dict(response.bias_map),
            "adjusted_temperature": response.adjusted_temperature,
            "adjusted_top_p": response.adjusted_top_p,
            "resonance_achieved": response.resonance_achieved
        }
    
    async def close(self):
        await self.channel.close()
