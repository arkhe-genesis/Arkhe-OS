import asyncio
import grpc
from concurrent import futures
import time
import numpy as np
# import arkhe_pb2
# import arkhe_pb2_grpc

# from tzinor.injection.logit_bias import UnifiedLogitBiasIntegrator
# from tzinor.distributed.nccl_sync import ResonanceSyncHook

class ResonanceServicer: # (arkhe_pb2_grpc.ResonanceServiceServicer):
    def __init__(self):
        self.active_sessions = {}  # session_id -> generator
        self.injectors = {}        # model_id -> injector
        self.config = {
            "k1": 0.015311,
            "k2": 0.05200,
            "lam": 0.001013,
            "rho_eq": 0.367879
        }
    
    async def Telemetry(self, request, context):
        """Stream de telemetria: envia atualizações a cada 100 ms."""
        session_id = request.session_id
        # Criar gerador de dados (exemplo: simulação)
        async def event_generator():
            phase = 0.0
            while True:
                # Simula evolução da fase (pode vir de um actor Ray ou fila)
                phase = (phase + 0.01) % (np.pi / 2)
                yield None # arkhe_pb2.TelemetryUpdate(
                #     phase=phase,
                #     amplitude=0.95,
                #     damping=0.9,
                #     sigma=0.1,
                #     tokens_processed=int(time.time() * 1000),
                #     timestamp=time.ctime()
                # )
                await asyncio.sleep(0.1)
        return event_generator()
    
    async def InjectBias(self, request, context):
        """Aplica bias em um modelo e retorna fase prevista."""
        model_id = request.model_id
        injector = self.injectors.get(model_id)
        if injector is None:
            # Inicializa injector para o modelo
            # injector = UnifiedLogitBiasIntegrator(provider=model_id, api_key=request.api_key)
            # self.injectors[model_id] = injector
            pass
        
        # Atualiza bias no injetor (configuração dinâmica)
        # injector.adapter.config.logit_bias = request.logit_bias
        # Simula predição da fase (em produção, rodaria uma inferência de teste)
        predicted_phase = 1.55  # mock
        return None # arkhe_pb2.BiasResponse(
        #     success=True,
        #     message="Bias applied",
        #     predicted_phase=predicted_phase
        # )
    
    async def UpdateConfig(self, request, context):
        """Atualiza constantes MUT globalmente."""
        self.config.update({
            "k1": request.k1,
            "k2": request.k2,
            "lam": request.lam,
            "rho_eq": request.rho_eq
        })
        # Propagar para todos os injectores ativos
        for injector in self.injectors.values():
            # injector.adapter.config.alpha_gravity = 2.0 * self.config["k1"] * 1e4
            # injector.adapter.config.beta_entropy = 0.5 * self.config["k2"] * 1e3
            pass
        return None # arkhe_pb2.ConfigAck(accepted=True, applied_timestamp=time.ctime())

import os

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    # arkhe_pb2_grpc.add_ResonanceServiceServicer_to_server(
    #     ResonanceServicer(), server
    # )
    
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
        server.add_secure_port('[::]:50051', server_credentials)
        print("qhttp:// gRPC server started on port 50051 with TLS")
    else:
        server.add_insecure_port('[::]:50051')
        print("qhttp:// gRPC server started on port 50051 (insecure)")
        
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
