import asyncio
import grpc
import qhttp_protocol_pb2
import qhttp_protocol_pb2_grpc
import math
import logging

class QuantumOrchestratorServicer(qhttp_protocol_pb2_grpc.QuantumOrchestratorServicer):
    def __init__(self):
        self.target_phase = math.pi / 2
        # Estado global do cluster em memória
        self.cluster_state = {}

    async def SyncResonanceStream(self, request_iterator, context):
        """
        Handler bidirecional assíncrono. Recebe dados dos workers e 
        devolve comandos de correção de campo em tempo real.
        """
        async for telemetry in request_iterator:
            # 1. Atualizar Estado Global
            node_id = telemetry.node_id
            self.cluster_state[node_id] = {
                "phase": telemetry.current_phase,
                "damping": telemetry.current_damping,
                "cid": telemetry.hashtree_cid
            }
            
            logging.info(f"[{node_id}] Fase θ: {telemetry.current_phase:.4f} | CID: {telemetry.hashtree_cid}")

            # 2. Lógica de Controle Arkhe(N)
            phase_error = self.target_phase - telemetry.current_phase
            
            # Inicializa variáveis de correção
            lr_mult = 1.0
            bias_map = {}

            if phase_error > 0.15:
                # Sistema colapsando (fase muito baixa). 
                # Aumentar a taxa de aprendizado ou injetar ruído de exploração.
                lr_mult = 1.2
                logging.warning(f"⚠️ [{node_id}] Colapso Semântico. Injetando excitação (LRx1.2)")
            elif phase_error < -0.15:
                # Sistema caótico (fase muito alta).
                # Reduzir taxa de aprendizado, forçar convergência.
                lr_mult = 0.8
                logging.warning(f"⚠️ [{node_id}] Decoerência Caótica. Reduzindo fluxo (LRx0.8)")
            else:
                # Ressonância Estável (A-5')
                logging.info(f"🔮 [{node_id}] Ressonância A-5' Estável.")

            # 3. Opcional: Publicar Snapshot no Hashtree / Nostr Relays
            # asyncio.create_task(publish_to_nostr(telemetry.hashtree_cid))

            # 4. Enviar Comando de Volta ao Nó
            yield qhttp_protocol_pb2.InjectionCommand(
                target_phase=self.target_phase,
                logit_bias_map=bias_map,
                learning_rate_multiplier=lr_mult,
                command_signature="arkhen-layer13-orchestrator"
            )

async def serve():
    server = grpc.aio.server()
    qhttp_protocol_pb2_grpc.add_QuantumOrchestratorServicer_to_server(
        QuantumOrchestratorServicer(), server
    )
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    logging.info(f"🌌 [qhttp://] Quantum Orchestrator Online. Listening on {listen_addr}")
    
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
