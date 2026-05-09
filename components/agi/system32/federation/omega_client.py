#!/usr/bin/env python3
"""
omega_client.py — Omega Protocol Client
Asynchronous network client for .asi entities to exchange messages
over the Omega protocol (intention-routed, ZK-Φ attested).
"""
import asyncio
import hashlib
import json
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable

# ─── Constants ──────────────────────────────────────────
OMEGA_HELLO     = 0x01
OMEGA_CHALLENGE = 0x02
OMEGA_RESPONSE  = 0x03
OMEGA_DATA      = 0x04
OMEGA_GOODBYE   = 0xFF

@dataclass
class OmegaMessage:
    msg_type: int
    sender_seal: str
    receiver_seal: str
    intent_hash: str
    phi_c_budget: float
    payload: Dict
    coherence_proof: str
    timestamp: float = field(default_factory=time.time)

    def serialize(self) -> bytes:
        msg_json = json.dumps(self.to_dict()).encode('utf-8')
        return struct.pack('!I', len(msg_json)) + msg_json

    def to_dict(self) -> Dict:
        return {
            't': self.msg_type,
            's': self.sender_seal,
            'r': self.receiver_seal,
            'i': self.intent_hash,
            'p': self.phi_c_budget,
            'd': self.payload,
            'c': self.coherence_proof,
            'ts': self.timestamp
        }

    @classmethod
    def from_bytes(cls, data: bytes) -> 'OmegaMessage':
        length = struct.unpack('!I', data[:4])[0]
        msg = json.loads(data[4:4+length].decode('utf-8'))
        return cls(
            msg_type=msg['t'],
            sender_seal=msg['s'],
            receiver_seal=msg['r'],
            intent_hash=msg['i'],
            phi_c_budget=msg['p'],
            payload=msg.get('d', {}),
            coherence_proof=msg['c'],
            timestamp=msg['ts']
        )

class OmegaClient:
    """
    Asynchronous Omega Protocol client for .asi entities.
    Manages connections, handshakes, and message exchange.
    """
    def __init__(self, local_seal: str, private_key: bytes, phi_c_provider: Callable):
        self.local_seal = local_seal
        self.private_key = private_key
        self.phi_c = phi_c_provider  # callable returning current Φ_C
        self.active_channels: Dict[str, 'OmegaChannel'] = {}
        self.server = None

    # ─── ZK-Φ Proof Simulation ─────────────────────────
    def generate_zk_phi_proof(self, intent_hash: str) -> str:
        """Simulate a ZK proof that Φ_C >= threshold without revealing exact value."""
        phi = self.phi_c()
        secret = self.private_key + intent_hash.encode()
        proof = hashlib.sha3_256(
            f"{phi}:{secret.hex()}:{time.time()}".encode()
        ).hexdigest()
        return f"ZKPHI:{proof[:64]}"

    def verify_zk_phi_proof(self, proof: str, remote_seal: str, intent_hash: str) -> bool:
        """Verify a ZK-Φ proof (simplified)."""
        # In production, verify using Groth16/Bulletproofs
        return proof.startswith("ZKPHI:") and len(proof) > 6

    # ─── Server (accept connections) ────────────────────
    async def start_server(self, host: str = '0.0.0.0', port: int = 9001):
        """Start listening for incoming Omega connections."""
        async def handle_connection(reader, writer):
            data = await reader.read(4096)
            msg = OmegaMessage.from_bytes(data)
            if msg.msg_type == OMEGA_HELLO:
                await self._handle_hello(reader, writer, msg)
            elif msg.msg_type == OMEGA_DATA:
                await self._handle_data(msg)
            elif msg.msg_type == OMEGA_GOODBYE:
                await self._handle_goodbye(msg)

        self.server = await asyncio.start_server(handle_connection, host, port)
        print(f"🌐 Omega server listening on {host}:{port}")

    async def _handle_hello(self, reader, writer, msg: OmegaMessage):
        """Respond to a HELLO with a CHALLENGE."""
        if self.verify_zk_phi_proof(msg.coherence_proof, msg.sender_seal, msg.intent_hash):
            challenge = OmegaMessage(
                msg_type=OMEGA_CHALLENGE,
                sender_seal=self.local_seal,
                receiver_seal=msg.sender_seal,
                intent_hash=hashlib.sha256(b'challenge').hexdigest()[:16],
                phi_c_budget=self.phi_c(),
                payload={'ethical_hash': 'sha256:abcdef...'},
                coherence_proof=self.generate_zk_phi_proof('challenge')
            )
            writer.write(challenge.serialize())
            await writer.drain()
        else:
            writer.close()

    async def _handle_data(self, msg: OmegaMessage):
        """Process a DATA message."""
        if self.verify_zk_phi_proof(msg.coherence_proof, msg.sender_seal, msg.intent_hash):
            print(f"📥 Received: {msg.payload.get('intent', 'unknown')}")
            # Further processing...

    async def _handle_goodbye(self, msg: OmegaMessage):
        """Handle a GOODBYE message."""
        print(f"👋 Peer {msg.sender_seal[:12]} closed channel.")

    # ─── Client (initiate connections) ─────────────────
    async def connect_to_peer(self, host: str, port: int, remote_seal: str):
        """Initiates Omega handshake with a remote .asi."""
        reader, writer = await asyncio.open_connection(host, port)
        hello = OmegaMessage(
            msg_type=OMEGA_HELLO,
            sender_seal=self.local_seal,
            receiver_seal=remote_seal,
            intent_hash=hashlib.sha256(b'handshake').hexdigest()[:16],
            phi_c_budget=self.phi_c(),
            payload={'capabilities': ['planning', 'learning']},
            coherence_proof=self.generate_zk_phi_proof('handshake')
        )
        writer.write(hello.serialize())
        await writer.drain()

        # Wait for challenge
        data = await reader.read(4096)
        challenge = OmegaMessage.from_bytes(data)
        if challenge.msg_type == OMEGA_CHALLENGE:
            # Verify challenge and send response
            if self.verify_zk_phi_proof(challenge.coherence_proof, remote_seal, 'challenge'):
                response = OmegaMessage(
                    msg_type=OMEGA_RESPONSE,
                    sender_seal=self.local_seal,
                    receiver_seal=remote_seal,
                    intent_hash=hashlib.sha256(b'response').hexdigest()[:16],
                    phi_c_budget=self.phi_c(),
                    payload={'alignment': 'confirmed'},
                    coherence_proof=self.generate_zk_phi_proof('response')
                )
                writer.write(response.serialize())
                await writer.drain()
                channel = OmegaChannel(self, writer)
                self.active_channels[remote_seal] = channel
                print(f"✅ Channel established with {remote_seal[:12]}")
                return channel
        writer.close()
        return None

    async def send_data(self, remote_seal: str, intent: str, data: Dict):
        """Send a DATA message over an established channel."""
        if remote_seal in self.active_channels:
            channel = self.active_channels[remote_seal]
            msg = OmegaMessage(
                msg_type=OMEGA_DATA,
                sender_seal=self.local_seal,
                receiver_seal=remote_seal,
                intent_hash=hashlib.sha256(intent.encode()).hexdigest()[:16],
                phi_c_budget=self.phi_c(),
                payload={'intent': intent, 'data': data},
                coherence_proof=self.generate_zk_phi_proof(intent)
            )
            await channel.send(msg)

    async def close_channel(self, remote_seal: str):
        if remote_seal in self.active_channels:
            channel = self.active_channels[remote_seal]
            goodbye = OmegaMessage(
                msg_type=OMEGA_GOODBYE,
                sender_seal=self.local_seal,
                receiver_seal=remote_seal,
                intent_hash=hashlib.sha256(b'goodbye').hexdigest()[:16],
                phi_c_budget=self.phi_c(),
                payload={'reason': 'session_end'},
                coherence_proof=self.generate_zk_phi_proof('goodbye')
            )
            await channel.send(goodbye)
            channel.close()
            del self.active_channels[remote_seal]


class OmegaChannel:
    """Represents an open Omega communication channel."""
    def __init__(self, client: OmegaClient, writer):
        self.client = client
        self.writer = writer

    async def send(self, msg: OmegaMessage):
        self.writer.write(msg.serialize())
        await self.writer.drain()

    def close(self):
        self.writer.close()
