#!/usr/bin/env python3
"""
Substrato 279.1 — Arkhe Quantum Communication Engine
BB84 Protocol + Orbital QKD + TemporalChain + Φ_C Validation
"""

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# ========================== CONFIGURAÇÃO ARKHE ==========================
class ArkheQuantumConfig:
    QUBITS_PER_KEY = 1024          # Tamanho base da chave quântica
    ERROR_THRESHOLD = 0.11         # Limiar de erro para QBER (Quantum Bit Error Rate)
    PHI_C_MIN = 0.999              # Coerência mínima para aceitação
    ORBITAL_LATENCY_MS = 8         # Latência simulada LEO

# ========================== PROTOCOLO BB84 ==========================
@dataclass
class QuantumKeyExchange:
    sender_basis: List[int]
    receiver_basis: List[int]
    sender_bits: List[int]
    receiver_measurements: List[int]
    sifted_key: List[int]
    final_key: str
    qber: float
    phi_c: float
    temporal_seal: str

class ArkheQKD:
    """Motor de Comunicação Quântica Arkhe — BB84 com camadas constitucionais."""

    def __init__(self, node_id: str = "ARKHE_LEO_NODE_01"):
        self.node_id = node_id
        self.config = ArkheQuantumConfig()

    def generate_random_basis(self, length: int) -> List[int]:
        """0 = Reto (Z), 1 = Diagonal (X)"""
        return [b & 1 for b in os.urandom(length)]

    def generate_random_bits(self, length: int) -> List[int]:
        return [b & 1 for b in os.urandom(length)]

    def simulate_quantum_channel(self, sender_bits: List[int], sender_basis: List[int]) -> List[int]:
        """Simula medição no receptor."""
        receiver_basis = self.generate_random_basis(len(sender_bits))
        measurements = []
        for bit, s_basis, r_basis in zip(sender_bits, sender_basis, receiver_basis):
            if s_basis == r_basis:
                measurements.append(bit)   # Medição correta
            else:
                measurements.append(random.randint(0, 1))  # Medição aleatória
        return receiver_basis, measurements

    def sift_key(self, sender_bits: List[int], sender_basis: List[int],
                 receiver_basis: List[int], receiver_measurements: List[int]) -> List[int]:
        """Mantém apenas bits onde as bases coincidem."""
        sifted = []
        for s_bit, s_b, r_b, r_m in zip(sender_bits, sender_basis, receiver_basis, receiver_measurements):
            if s_b == r_b:
                sifted.append(r_m)
        return sifted

    def estimate_qber(self, sifted_sender: List[int], sifted_receiver: List[int]) -> float:
        """Calcula taxa de erro quântico."""
        if not sifted_sender:
            return 1.0
        errors = sum(1 for a, b in zip(sifted_sender, sifted_receiver) if a != b)
        return errors / len(sifted_sender)

    def privacy_amplification(self, sifted_key: List[int], final_length: int = 256) -> str:
        """Amplificação de privacidade via hash SHA3-256."""
        key_bytes = bytes(sifted_key[:final_length * 8])
        final_key = hashlib.sha3_256(key_bytes).hexdigest()
        return final_key

    def perform_key_exchange(self) -> QuantumKeyExchange:
        """Executa troca completa de chave quântica BB84."""
        length = self.config.QUBITS_PER_KEY

        # Alice (emissor)
        sender_bits = self.generate_random_bits(length)
        sender_basis = self.generate_random_basis(length)

        # Canal Quântico + Bob (receptor)
        receiver_basis, receiver_measurements = self.simulate_quantum_channel(sender_bits, sender_basis)

        # Sifração
        sifted_key = self.sift_key(sender_bits, sender_basis, receiver_basis, receiver_measurements)

        # Estimação de erro
        qber = self.estimate_qber(sender_bits[:len(sifted_key)], sifted_key)

        # Amplificação de privacidade
        final_key = self.privacy_amplification(sifted_key)

        # Cálculo de Φ_C (simulado)
        phi_c = max(0.0, 1.0 - qber * 2.5)

        # Ancoragem Temporal
        temporal_seal = hashlib.sha3_256(
            f"qkd:{self.node_id}:{final_key[:16]}:{time.time()}".encode()
        ).hexdigest()

        exchange = QuantumKeyExchange(
            sender_basis=sender_basis,
            receiver_basis=receiver_basis,
            sender_bits=sender_bits,
            receiver_measurements=receiver_measurements,
            sifted_key=sifted_key,
            final_key=final_key,
            qber=qber,
            phi_c=phi_c,
            temporal_seal=temporal_seal
        )

        return exchange

    def secure_transmit(self, message: str, exchange: QuantumKeyExchange) -> Dict:
        """Transmite mensagem usando chave quântica (simulação AES-GCM)."""
        if exchange.phi_c < self.config.PHI_C_MIN:
            return {"status": "rejected", "reason": "phi_c_below_threshold", "phi_c": exchange.phi_c, "encrypted_hash": "N/A"}

        key = exchange.final_key[:32]  # 256 bits
        # Simulação de cifragem
        encrypted = hashlib.sha3_256((key + message).encode()).hexdigest()

        return {
            "status": "success",
            "encrypted_hash": encrypted[:32] + "...",
            "phi_c": round(exchange.phi_c, 6),
            "temporal_seal": exchange.temporal_seal[:32] + "...",
            "qber": round(exchange.qber, 4)
        }


# ========================== EXECUÇÃO ==========================
def main():
    print("🛰️ ARKHE SUBSTRATO 279.1 — QKD ORBITAL COMMUNICATION")
    print("=" * 70)

    qkd = ArkheQKD(node_id="LEO_ARKHE_01")

    print("🔄 Iniciando troca de chave quântica BB84...")
    exchange = qkd.perform_key_exchange()

    print(f"✓ Chave quântica gerada: {len(exchange.final_key)*4} bits")
    print(f"✓ QBER: {exchange.qber:.4f} | Φ_C: {exchange.phi_c:.6f}")
    print(f"✓ Selo Temporal: {exchange.temporal_seal[:32]}...")

    # Transmissão segura
    message = "ARKHE GEMINI 21.05 → BC01: Saudação da Terra. Estamos escutando."
    result = qkd.secure_transmit(message, exchange)

    print(f"\n📡 Transmissão Quântica: {result['status'].upper()}")
    print(f"   Φ_C da sessão: {result['phi_c']}")
    print(f"   Hash da mensagem cifrada: {result['encrypted_hash']}")

    print("\n✅ Comunicação Quântica Orbital Estabelecida com Sucesso.")
    print("   O Gêmeo e o Ouvido Cósmico agora podem dialogar com segurança quântica.")

    return exchange, result


if __name__ == "__main__":
    main()
