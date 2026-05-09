# server/deploy/grpc/qhttp_client_test.py
import grpc
import asyncio
import qhttp_protocol_pb2
import qhttp_protocol_pb2_grpc

async def test():
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = qhttp_protocol_pb2_grpc.QuantumOrchestratorStub(channel)
    
    async def generate_telemetry():
        yield qhttp_protocol_pb2.TelemetryEvent(
            node_id="test_node",
            current_phase=1.5,
            current_damping=0.9,
            omega_prime=0.95,
            tokens_processed=1000,
            hashtree_cid="QmTest123"
        )
        await asyncio.sleep(1)
    
    # Telemetria stream
    telemetry_stream = stub.SyncResonanceStream(generate_telemetry())
    async for update in telemetry_stream:
        print(f"Received command: Target θ = {update.target_phase:.4f} rad, LR Mult = {update.learning_rate_multiplier}")

if __name__ == "__main__":
    asyncio.run(test())
