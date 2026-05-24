import grpc

class ConsensusClient:
    def __init__(self, endpoint: str = "grpc://consensus-latam.arkhe.org"):
        self.endpoint = endpoint
        self.channel = None

    def connect(self):
        # Establish an insecure gRPC channel
        target = self.endpoint.replace("grpc://", "")
        self.channel = grpc.insecure_channel(target)
        print(f"Connected to {self.endpoint}")

consensus_client = ConsensusClient()
