from typing import Dict, Any
import time

class EncodedMessage:
    def __init__(self, payload: bytes, metadata: Dict, total_size_bytes: int):
        self.payload = payload
        self.metadata = metadata
        self.total_size_bytes = total_size_bytes

def compress_data(message: Dict, ratio: int) -> bytes:
    return str(message).encode()

def encrypt_with_pqc(compressed: bytes, key_type: str, signature_type: str) -> bytes:
    return b"encrypted_" + compressed

class QHTTPAdaptiveEncoder:
    """Codificador adaptativo para qhttp:// que detecta condições do enlace e ajusta protocolo."""

    ENCODING_MODES = {
        "SYNC": {
            "max_latency_s": 3.0,
            "min_throughput_mbps": 100,
            "consensus_model": "tendermint_sync",
            "compression_ratio": 1,
            "crypto_overhead_kb": 0.5,
            "use_case": "Interior zone operations"
        },
        "SEMI_SYNC": {
            "max_latency_s": 1500,  # 25 min
            "min_throughput_mbps": 1,
            "consensus_model": "tendermint_semi_sync",
            "compression_ratio": 10,
            "crypto_overhead_kb": 1.0,
            "use_case": "Mars zone operations"
        },
        "STORE_FORWARD": {
            "max_latency_s": 5000,  # 83 min
            "min_throughput_kbps": 100,
            "consensus_model": "hybrid_crdt_batch",
            "compression_ratio": 100,
            "crypto_overhead_kb": 2.0,
            "use_case": "Belt/Jovian zone operations"
        },
        "ASYNC_CRDT": {
            "max_latency_s": float('inf'),
            "min_throughput_bps": 10,
            "consensus_model": "pure_crdt_merkle",
            "compression_ratio": 1000,
            "crypto_overhead_kb": 3.3,  # ML-DSA signatures for critical ops
            "use_case": "Outer system (Saturn+) operations"
        }
    }

    def select_encoding_mode(self, link_metrics: Dict) -> str:
        """Seleciona modo de encoding baseado em métricas do enlace em tempo real."""
        latency_s = link_metrics.get("rtt_s", float('inf'))
        throughput_bps = link_metrics.get("throughput_bps", 0)

        # Avaliar modos em ordem de preferência (mais síncrono primeiro)
        for mode_name, mode_params in self.ENCODING_MODES.items():
            if (latency_s <= mode_params["max_latency_s"] and
                throughput_bps >= mode_params.get("min_throughput_bps", 0) and
                throughput_bps >= mode_params.get("min_throughput_kbps", 0) * 1000 and
                throughput_bps >= mode_params.get("min_throughput_mbps", 0) * 1000000):
                return mode_name

        # Fallback para modo mais assíncrono se nenhum outro se adequar
        return "ASYNC_CRDT"

    def _compute_expected_finality(self, mode: str) -> int:
        if mode == "SYNC": return 3
        if mode == "SEMI_SYNC": return 1500
        if mode == "STORE_FORWARD": return 7200
        return 1036800

    def encode_message(self, message: Dict, mode: str) -> EncodedMessage:
        """Codifica mensagem conforme modo selecionado."""
        params = self.ENCODING_MODES[mode]

        # 1. Aplicar compressão
        compressed = compress_data(message, ratio=params["compression_ratio"])

        # 2. Aplicar criptografia PQC adaptativa
        if mode in ["SYNC", "SEMI_SYNC"]:
            # Baixo overhead: LMS para assinaturas frequentes
            encrypted = encrypt_with_pqc(compressed, key_type="ML-KEM-1024",
                                        signature_type="LMS-XMSS")
        else:
            # Alto overhead aceitável: ML-DSA para operações críticas
            encrypted = encrypt_with_pqc(compressed, key_type="ML-KEM-1024",
                                        signature_type="ML-DSA-87")

        # 3. Adicionar metadados de consenso e finalidade
        metadata = {
            "encoding_mode": mode,
            "consensus_model": params["consensus_model"],
            "expected_finality": self._compute_expected_finality(mode),
            "compression_ratio_applied": params["compression_ratio"],
            "timestamp": time.time()
        }

        return EncodedMessage(
            payload=encrypted,
            metadata=metadata,
            total_size_bytes=len(encrypted) + len(str(metadata))
        )
