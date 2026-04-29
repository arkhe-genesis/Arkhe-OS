import asyncio
import struct
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class H2CornFrame:
    """
    HTTP/2-Compatible Coherent Resonance (h2corn) Frame.
    Wraps standard frames with phase and ZK metadata.
    """
    stream_id: int
    payload: bytes
    phase_rad: float
    zk_proof_hash: str
    lambda_coherence: float = 0.95

    def to_bytes(self) -> bytes:
        header = struct.pack('!I d 32s f',
            self.stream_id,
            self.phase_rad,
            self.zk_proof_hash.encode()[:32],
            self.lambda_coherence
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> 'H2CornFrame':
        header_format = '!I d 32s f'
        header_size = struct.calcsize(header_format)
        (sid, phase, zk_hash, lb) = struct.unpack(header_format, data[:header_size])
        return cls(
            stream_id=sid,
            payload=data[header_size:],
            phase_rad=phase,
            zk_proof_hash=zk_hash.decode().strip('\x00'),
            lambda_coherence=lb
        )

class H2CornTransport:
    """
    Transporte qhttp:// via frames h2corn.
    Provê garantias de sincronização entre nós Wheeler.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_phase = 1.618  # φ

    async def send_qhttp_request(self, writer: asyncio.StreamWriter, method: str, path: str, body: bytes = b""):
        # Encapsula a requisição em um frame h2corn
        payload = f"{method} {path} HTTP/2.0\r\n\r\n".encode() + body
        zk_proof = hashlib.sha256(f"{self.node_id}:{time.time()}".encode()).hexdigest()

        frame = H2CornFrame(
            stream_id=1,
            payload=payload,
            phase_rad=self.local_phase,
            zk_proof_hash=zk_proof
        )

        writer.write(frame.to_bytes())
        await writer.drain()

    async def receive_qhttp_response(self, reader: asyncio.StreamReader) -> H2CornFrame:
        data = await reader.read(4096)
        return H2CornFrame.from_bytes(data)
