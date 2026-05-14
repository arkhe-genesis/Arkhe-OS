import asyncio
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass

from arkhe.immersive.bci_neural_interface import NeuralStateDecoder, NeuralCommand
from arkhe.network.qkd_protocol import QKDKeyDistribution, QKDSession, QKDProtocol

@dataclass
class AuthResult:
    success: bool
    confidence: float
    session_id: Optional[str]
    temporal_anchor: Optional[str]

class BCIQKDAuthenticator:
    """
    Implements BCI+QKD biometric authentication (v7.4.0 integration).
    Uses NeuralStateDecoder to extract a neural signal hash which is then used to
    establish a highly secure QKD session.
    """
    def __init__(self, neural_decoder: NeuralStateDecoder, qkd_distributor: QKDKeyDistribution):
        self.decoder = neural_decoder
        self.qkd = qkd_distributor

    async def authenticate(self, neural_signal: np.ndarray, ground_station_a: str, ground_station_b: str) -> AuthResult:
        # First, decode neural command to get biometric hash and confidence
        command = await self.decoder.decode_command(neural_signal, user_phi_c=0.99)

        if not command or command.confidence < 0.8:
            return AuthResult(success=False, confidence=command.confidence if command else 0.0, session_id=None, temporal_anchor=None)

        # Use neural hash as a biometric factor to establish QKD session
        session = await self.qkd.establish_qkd_session(
            station_a=f"{ground_station_a}_{command.raw_signal_hash[:8]}",
            station_b=ground_station_b,
            protocol=QKDProtocol.E91,
            key_length=256
        )

        return AuthResult(
            success=True,
            confidence=command.confidence,
            session_id=session.session_id,
            temporal_anchor=session.temporal_anchor
        )
