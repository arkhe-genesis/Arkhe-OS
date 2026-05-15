from dataclasses import dataclass
import os

@dataclass
class ServiceConfig:
    service_name: str = os.getenv("ARKHE_SERVICE_NAME", "arkhe-generic")
    phi_bus_endpoint: str = os.getenv("ARKHE_PHI_BUS_ENDPOINT", "grpc://phi-bus.arkhe:8052")
    temporal_endpoint: str = os.getenv("ARKHE_TEMPORAL_ENDPOINT", "grpc://temporal-chain.arkhe:8051")
    qbus_endpoint: str = os.getenv("ARKHE_QBUS_ENDPOINT", "http://qbus-sidecar.arkhe:8088")
    quantum_enabled: bool = os.getenv("ARKHE_QUANTUM_ENABLED", "True").lower() == "true"
    pqc_algorithm: str = os.getenv("ARKHE_PQC_ALGO", "Dilithium3")
    quantum_witness_photons: int = int(os.getenv("ARKHE_QUANTUM_PHOTONS", "256"))

def load_config() -> ServiceConfig:
    return ServiceConfig()
