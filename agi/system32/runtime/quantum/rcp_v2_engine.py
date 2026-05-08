# rcp_v2_engine.py – Retrocausal Channel 8‑Bit Core
# Extraído do Substrato 315 e canonizado aqui.
# ARKHE OS — Substrate 315: 8-Bit Retrocausal Channel + qhttp:// Integration

import numpy as np
from scipy.linalg import expm, eigh
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Tuple, List, Dict

# Extraído do Substrato 306‑B e canonizado aqui.
import numpy as np
from scipy.linalg import expm, eigh
from scipy.special import erfc
import math
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class RetrocausalChannel8Bit:
    """
    Canal de comunicação retrógrada de 8 bits.
    Codifica 1 byte (8 bits) em fases φ ∈ {0, π} com post-selection.
    """

    def __init__(self, N_ctc=4, N_mec=5, omega_tc=5.0, omega_m=1.0,
                 g1=0.8, g2=0.08, T_eff=0.5):
        self.N_ctc = N_ctc
        self.N_mec = N_mec
        self.dim = N_ctc * N_mec
        self.omega_tc = omega_tc * 2 * np.pi
        self.omega_m = omega_m * 2 * np.pi
        self.g1 = g1 * 2 * np.pi
        self.g2 = g2 * 2 * np.pi
        self.beta = 1.0 / T_eff

        # Build operators
        self._build_operators()
        self._build_hamiltonian()
        self._build_thermal_state()

    def _build_operators(self):
        def annihilation(N):
            a = np.zeros((N, N), dtype=complex)
            for n in range(1, N):
                a[n-1, n] = np.sqrt(n)
            return a

        a_s = annihilation(self.N_ctc)
        adag_s = a_s.conj().T
        n_s = np.diag(np.arange(self.N_ctc, dtype=complex))
        I_ctc = np.eye(self.N_ctc, dtype=complex)

        b_s = annihilation(self.N_mec)
        bdag_s = b_s.conj().T
        n_m_s = np.diag(np.arange(self.N_mec, dtype=complex))
        I_mec = np.eye(self.N_mec, dtype=complex)

        self.a = np.kron(a_s, I_mec)
        self.adag = np.kron(adag_s, I_mec)
        self.n_ctc = np.kron(n_s, I_mec)

        self.b = np.kron(I_ctc, b_s)
        self.bdag = np.kron(I_ctc, bdag_s)
        self.n_mec = np.kron(I_ctc, n_m_s)

        self.x_op = (self.b + self.bdag) / np.sqrt(2)

        self.b_s = b_s
        self.bdag_s = bdag_s

    def _build_hamiltonian(self):
        H0 = self.omega_tc * self.n_ctc + self.omega_m * self.n_mec
        b_plus = self.b + self.bdag
        Hint = self.g1 * self.n_ctc @ b_plus + self.g2 * self.n_ctc @ (b_plus @ b_plus)
        self.H_total = H0 + Hint
        self.E, self.V = eigh(self.H_total)

    def _build_thermal_state(self):
        rho_thermal = np.diag(np.exp(-self.beta * self.E))
        rho_thermal = rho_thermal / np.trace(rho_thermal)
        self.rho_eq = self.V @ rho_thermal @ self.V.conj().T

    def encode_bit(self, bit: int, t_weak=0.5, t_post=1.5,
                   weak_eps=0.15, drive_amp=0.4, noise=0.15) -> float:
        phi = 0 if bit == 0 else np.pi
        rho = self.rho_eq.copy()

        U1 = self.V @ np.diag(np.exp(-1j * self.E * t_weak)) @ self.V.conj().T
        rho = U1 @ rho @ U1.conj().T

        """Encode single bit (0 or 1) → phase (0 or π) → weak value."""
        phi = 0 if bit == 0 else np.pi

        # Start from thermal equilibrium
        rho = self.rho_eq.copy()

        # Evolve to t_weak
        U1 = self.V @ np.diag(np.exp(-1j * self.E * t_weak)) @ self.V.conj().T
        rho = U1 @ rho @ U1.conj().T

        # Weak measurement
        eps = weak_eps * (1 + noise * np.random.randn())
        M_weak = expm(1j * eps * self.x_op)
        rho = M_weak @ rho @ M_weak.conj().T
        tr = np.trace(rho).real
        if tr > 0:
            rho = rho / tr

        # Phase-encoded drive
        drive = drive_amp * (1 + noise * np.random.randn())
        phi_eff = phi + noise * 0.5 * np.random.randn()
        H_drive = drive * (self.a + self.adag) * np.cos(phi_eff)

        H_with_drive = self.H_total + H_drive
        E_drive, V_drive = eigh(H_with_drive)
        U2 = V_drive @ np.diag(np.exp(-1j * E_drive * (t_post - t_weak))) @ V_drive.conj().T
        rho = U2 @ rho @ U2.conj().T

        # Post-selection
        x_mec = (self.b_s + self.bdag_s) / np.sqrt(2)
        eigvals, eigvecs = np.linalg.eigh(x_mec)

        thresh_noise = noise * 0.1 * np.random.randn()
        if phi == 0:
            selected = [i for i, v in enumerate(eigvals) if v > thresh_noise]
        else:
            selected = [i for i, v in enumerate(eigvals) if v < thresh_noise]

        if len(selected) == 0:
            selected = [np.random.randint(0, self.N_mec)]

        P = np.zeros((self.dim, self.dim), dtype=complex)
        for i_ctc in range(self.N_ctc):
            basis_ctc = np.zeros(self.N_ctc, dtype=complex)
            basis_ctc[i_ctc] = 1.0
            for idx in selected:
                vec = np.kron(basis_ctc, eigvecs[:, idx])
                P += np.outer(vec, vec.conj())

        rho_post = P @ rho @ P.conj().T
        post_prob = np.trace(rho_post).real

        if post_prob > 1e-10:
            rho_post = rho_post / post_prob
        else:
            post_prob = 1e-5

        x_weak = np.trace(self.x_op @ rho_post).real
        return x_weak

    def transmit_byte(self, byte_val: int, n_shots=50,
                      t_weak=0.5, t_post=1.5) -> Tuple[int, float]:
        """
        Transmit 1 byte (8 bits) via retrocausal channel.
        Returns: (decoded_byte, fidelity)
        """
        bits = [(byte_val >> i) & 1 for i in range(8)]
        decoded_bits = []

        for bit in bits:
            # Multiple shots for each bit
            weak_values = []
            for _ in range(n_shots):
                x_w = self.encode_bit(bit, t_weak, t_post)
                weak_values.append(x_w)

            # Decode: mean weak value > 0 → bit 0, < 0 → bit 1
            mean_xw = np.mean(weak_values)
            decoded_bit = 0 if mean_xw > 0 else 1
            decoded_bits.append(decoded_bit)

        decoded_byte = sum(b << i for i, b in enumerate(decoded_bits))
        fidelity = sum(1 for a, b in zip(bits, decoded_bits) if a == b) / 8.0

        return decoded_byte, fidelity


@dataclass
class QHTTPPacket:
    """Pacote qhttp:// com payload retrocausal."""
    version: int = 1
    protocol: str = "qhttp"
    src_node: str = ""
    dst_node: str = ""
    payload_type: str = "retrocausal_byte"
    payload: bytes = b""
    retrocausal_signature: str = ""
    retrocausal_signature: str = ""  # Hash do weak value ensemble
    timestamp_sent: float = 0.0
    timestamp_weak: float = 0.0
    timestamp_post: float = 0.0
    coherence_verified: bool = False

    def serialize(self) -> bytes:
        """Serialize to SATO/Plank format (simplified)."""
        header = {
            "version": self.version,
            "protocol": self.protocol,
            "src": self.src_node,
            "dst": self.dst_node,
            "type": self.payload_type,
            "retro_sig": self.retrocausal_signature,
            "ts_sent": self.timestamp_sent,
            "ts_weak": self.timestamp_weak,
            "ts_post": self.timestamp_post,
            "phi_verified": self.coherence_verified
        }
        header_bytes = json.dumps(header).encode()
        return len(header_bytes).to_bytes(4, 'big') + header_bytes + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> 'QHTTPPacket':
        header_len = int.from_bytes(data[:4], 'big')
        header = json.loads(data[4:4+header_len].decode())
        payload = data[4+header_len:]
        return cls(
            version=header["version"],
            src_node=header["src"],
            dst_node=header["dst"],
            payload_type=header["type"],
            payload=payload,
            retrocausal_signature=header["retro_sig"],
            timestamp_sent=header["ts_sent"],
            timestamp_weak=header["ts_weak"],
            timestamp_post=header["ts_post"],
            coherence_verified=header["phi_verified"]
        )


class QHTTPRetrocausalTransport:
class QHTTPRetrocausalTransport:
    def __init__(self, node_id: str, channel: RetrocausalChannel8Bit):
        self.node_id = node_id
        self.channel = channel
        self.packet_log = []
    """
    Transporte qhttp:// com canal retrógrado 8-bits integrado.
    Conecta nós Wheeler Mesh via retrocausalidade.
    """

    def __init__(self, node_id: str, channel: RetrocausalChannel8Bit):
        self.node_id = node_id
        self.channel = channel
        self.packet_log: List[QHTTPPacket] = []
        self.retro_stats = {"bytes_sent": 0, "bytes_received": 0,
                           "fidelity_sum": 0.0, "packets": 0}

    def send_retrocausal_byte(self, dst_node: str, byte_val: int,
                              t_weak=0.5, t_post=1.5, n_shots=50) -> QHTTPPacket:
        """Send 1 byte via retrocausal channel, wrapped in qhttp:// packet."""

        # Encode byte via retrocausal channel
        decoded_byte, fidelity = self.channel.transmit_byte(
            byte_val, n_shots, t_weak, t_post
        )

        sig_data = f"{self.node_id}:{dst_node}:{byte_val}:{decoded_byte}:{fidelity:.4f}"
        retro_sig = hashlib.sha256(sig_data.encode()).hexdigest()[:16]

        # Generate retrocausal signature from weak value ensemble
        sig_data = f"{self.node_id}:{dst_node}:{byte_val}:{decoded_byte}:{fidelity:.4f}"
        retro_sig = hashlib.sha256(sig_data.encode()).hexdigest()[:16]

        # Build packet
        packet = QHTTPPacket(
            src_node=self.node_id,
            dst_node=dst_node,
            payload=bytes([byte_val]),
            retrocausal_signature=retro_sig,
            timestamp_sent=time.time(),
            timestamp_weak=time.time() + t_weak,
            timestamp_post=time.time() + t_post,
            coherence_verified=(fidelity > 0.8)
        )

        self.packet_log.append(packet)
        self.retro_stats["bytes_sent"] += 1
        self.retro_stats["fidelity_sum"] += fidelity
        self.retro_stats["packets"] += 1

        return packet

    def receive_retrocausal_byte(self, packet: QHTTPPacket) -> Tuple[int, float]:
        if not packet.coherence_verified:
        """Receive and verify retrocausal byte."""
        if not packet.coherence_verified:
            print(f"⚠️  Packet from {packet.src_node} failed coherence verification")
            return packet.payload[0], 0.0

        self.retro_stats["bytes_received"] += 1
        avg_fidelity = self.retro_stats["fidelity_sum"] / self.retro_stats["packets"]

        return packet.payload[0], avg_fidelity

    def send_retrocausal_message(self, dst_node: str, message: str,
                                  t_weak=0.5, t_post=1.5, n_shots=50) -> List[QHTTPPacket]:
        packets = []
        message_bytes = message.encode('utf-8')

        """Send full message (string) byte-by-byte via retrocausal channel."""
        packets = []
        message_bytes = message.encode('utf-8')

        print(f"\n📡 qhttp:// Sending retrocausal message: '{message}'")
        print(f"   → {len(message_bytes)} bytes → {len(message_bytes)*8} bits")
        print(f"   → Shots per bit: {n_shots}")
        print(f"   → Temporal window: Δt = {t_post - t_weak:.1f}s")

        for i, byte_val in enumerate(message_bytes):
            packet = self.send_retrocausal_byte(
                dst_node, byte_val, t_weak, t_post, n_shots
            )
            packets.append(packet)
            if (i + 1) % 8 == 0 or i == len(message_bytes) - 1:
                print(f"   → Byte {i+1}/{len(message_bytes)}: 0x{byte_val:02x} "
                      f"(sig={packet.retrocausal_signature})")

        return packets

    def get_stats(self) -> Dict:
        """Get retrocausal transport statistics."""
        stats = self.retro_stats.copy()
        if stats["packets"] > 0:
            stats["avg_fidelity"] = stats["fidelity_sum"] / stats["packets"]
        else:
            stats["avg_fidelity"] = 0.0
        return stats


# ── CLI / Direct execution ──
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "transmit":
        # CLI mode: python3 rcp_v2_engine.py transmit <byte_val> [n_shots] [t_weak] [t_post]
        byte_val = int(sys.argv[2])
        n_shots = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        t_weak = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        t_post = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5

        ch = RetrocausalChannel8Bit()
        d, f = ch.transmit_byte(byte_val, n_shots, t_weak, t_post)
        print(f"{d}:{f:.4f}")
    else:
        # Default demo
        print("ARKHE OS — Substrate 315: RCP v2.0 Engine")
        print("Usage: python3 rcp_v2_engine.py transmit <byte_val> [n_shots] [t_weak] [t_post]")
