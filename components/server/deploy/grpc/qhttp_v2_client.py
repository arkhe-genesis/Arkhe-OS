import grpc
import asyncio
import qhttp_v2_pb2
import qhttp_v2_pb2_grpc
import time

import os

class QHTTPResonanceClient:
    """
    Cliente assíncrono que conecta ao cluster Arkhe(N) via qhttp://
    e aplica logit bias em tempo real a APIs de modelos fechados.
    """
    
    def __init__(self, target="qhttp-telemetry.teknet.svc:50051"):
        cert_path = os.environ.get('GRPC_CERT_PATH')
        
        if cert_path:
            with open(cert_path, 'rb') as f:
                trusted_certs = f.read()
            credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
            self.channel = grpc.aio.secure_channel(target, credentials)
            print(f"Connecting to {target} with TLS")
        else:
            self.channel = grpc.aio.insecure_channel(target)
            print(f"Connecting to {target} (insecure)")
            
        self.stub = qhttp_v2_pb2_grpc.QuantumResonanceStub(self.channel)
        self.current_bias = {}
        self.phase_estimate = 0.0
        
    async def telemetry_stream(self):
        """
        Mantém conexão persistente com o cluster, recebendo
        atualizações de fase e injetando bias.
        """
        async def generate_telemetry():
            while True:
                yield qhttp_v2_pb2.TelemetryPacket(
                    node_id="layer8_client",
                    theta=self.phase_estimate,
                    timestamp_ns=time.time_ns()
                )
                await asyncio.sleep(0.05)
        
        async for control in self.stub.ResonanceChannel(generate_telemetry()):
            if control.HasField("bias_inject"):
                self.current_bias = dict(control.bias_inject.token_bias)
                print(f"🔮 Bias atualizado: θ={self.phase_estimate:.4f}, "
                      f"bias_strength={sum(abs(v) for v in self.current_bias.values())}")
            
            elif control.HasField("emergency"):
                print(f"🚨 EMERGÊNCIA: {control.emergency.reason}")
                break
    
    def get_current_bias(self):
        return self.current_bias

# Uso em API real (ex: OpenAI)
async def generate_with_resonance(prompt, client):
    bias = client.get_current_bias()
    # response = await openai.ChatCompletion.acreate(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}],
    #     logit_bias=bias,
    #     temperature=0.7 * (1 - abs(client.phase_estimate - 1.57)/1.57)  # Adaptativo
    # )
    # return response
    return {"status": "mocked response"}
