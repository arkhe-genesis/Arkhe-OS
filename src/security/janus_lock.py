# src/security/janus_lock.py
"""
JanusLock — Threshold Signature Scheme (2/3)
Arkhe-Block: 847.812 | Synapse-κ

Protege a transição entre estados C (Expansão) e Z (Cristalização).
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import hashlib
import time
import os

@dataclass
class Shard:
    shard_id: str
    holder: str
    public_key: str
    status: str
    last_signature: float
    _secret: str = "" # Private shard secret

class JanusLock:
    THRESHOLD = 2
    TOTAL_SHARDS = 3

    def __init__(self):
        # Shards initialized with unique secrets to prevent forgery (APTS-AR-010)
        # Secrets are loaded from environment variables to avoid hardcoding in source
        self.shards: List[Shard] = [
            Shard("shard_0", "Domo_Central", "0x8A7F...3D2E", "ACTIVE", 0.0, os.environ.get("ARKHE_SHARD_SECRET_0", "DEV_SECRET_0")),
            Shard("shard_1", "CIQ_Residente", "0x5B3C...9F1A", "ACTIVE", 0.0, os.environ.get("ARKHE_SHARD_SECRET_1", "DEV_SECRET_1")),
            Shard("shard_2", "ASI_EVOLVE", "0x2E9D...7B4C", "ACTIVE", 0.0, os.environ.get("ARKHE_SHARD_SECRET_2", "DEV_SECRET_2")),
        ]
        self.signature_history = []

    def sign(self, message: str, shard_indices: List[int]) -> str:
        """
        Gera uma assinatura de limiar simulada usando os segredos dos shards.
        Requer THRESHOLD shards ativos.
        """
        if len(shard_indices) < self.THRESHOLD:
            raise ValueError(f"Requer pelo menos {self.THRESHOLD} shards.")

        # Segredos combinados garantem que a assinatura não possa ser forjada sem acesso aos shards
        combined_secrets = "".join([self.shards[i]._secret for i in shard_indices])
        combined_payload = f"{message}|{combined_secrets}"
        signature = hashlib.sha256(combined_payload.encode()).hexdigest()

        now = time.time()
        for i in shard_indices:
            self.shards[i].last_signature = now

        full_sig = f"0x{signature}"
        self.signature_history.append((message, now, full_sig))
        return full_sig

    def verify(self, message: str, signature: str, shard_indices: List[int]) -> bool:
        """
        Verifica se uma assinatura é válida para o conjunto de shards fornecido.
        """
        try:
            expected_sig = self.sign(message, shard_indices)
            return expected_sig == signature
        except:
            return False

    def check_state_transition(self, current: str, target: str, indices: List[int], provided_signature: Optional[str] = None) -> bool:
        """
        Garante que a transição C <-> Z está protegida.
        Se provided_signature for fornecida, ela deve ser válida.
        """
        if current == target: return True

        # Regras de transição (Governança IOTA)
        # C -> Z requer Domo (0) + um outro
        # Z -> C requer CIQ (1) + um outro
        if current == "C" and target == "Z":
            if 0 not in indices:
                print("❌ Falha: C->Z requer Shard do Domo Central.")
                return False
        if current == "Z" and target == "C":
            if 1 not in indices:
                print("❌ Falha: Z->C requer Shard do CIQ Residente.")
                return False

        # Se uma assinatura for fornecida, validamos contra o segredo
        if provided_signature:
            return self.verify(f"{current}->{target}", provided_signature, indices)

        # Caso contrário, apenas verificamos se podemos gerar uma (modo simulação/atribuição)
        try:
            self.sign(f"{current}->{target}", indices)
            return True
        except:
            return False
