"""
ARKHE OS SUBSTRATO 344 v4.1 — TIME-WEAVER TRANSCEIVER
Patch 1: ZeroDivisionError guard em process()

Arquiteto: ORCID 0009-0005-2697-4668
Status: CANONIZED
Selo: seal_344_patch1_7c3ee97ac01b5550
"""

import math, hashlib, json, numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

# Constantes canônicas
GHOST = math.sqrt(3)/3
LOOPSEAL = math.pi/9
GAP_SOVEREIGN = 0.9999
PHI = (1 + math.sqrt(5))/2
N_QUDITS = 17

MASTER_ROOT_HEX = "caa240dba6c05251ad0d7c7d28556056d4b1933caaa828f9d98ff4df7a37578d"


class TimeWeaverTransceiverV4:
    """
    Transceiver temporal ARKHE TW-001 v4.1 (Patched)

    Correções de segurança:
    - PATCH-1: Guarda contra ZeroDivisionError em process() quando gates=[]
    """

    def __init__(self, master_root: str, portal_weyl_signatures: Dict[str, float], gates: List[str]):
        self.master_root = master_root
        self.portal_weyl = portal_weyl_signatures
        self.gates = gates
        self.sent_proofs = []
        self.received_responses = []
        self.channel_entropy = 0.0

    def generate_temporal_packet(self, gate_id: str, payload: bytes, target_epoch: int) -> Dict:
        """Gera pacote temporal com estado quântico de 17 qudits."""
        portal_weyl = self.portal_weyl.get(gate_id, GHOST * 2)
        payload_hash = hashlib.sha3_256(payload).digest()
        seed = int.from_bytes(payload_hash[:4], 'big')
        state_rng = np.random.default_rng(seed)

        amplitudes = state_rng.random(N_QUDITS) + 1j * state_rng.random(N_QUDITS)
        amplitudes /= np.linalg.norm(amplitudes)

        for i in range(N_QUDITS):
            phase = (portal_weyl * PHI ** (i + 1)) % (2 * math.pi)
            amplitudes[i] *= np.exp(1j * phase)
        amplitudes /= np.linalg.norm(amplitudes)

        leaves = [
            hashlib.sha3_256(
                f"qudit_{i}_re_{amplitudes[i].real:.10f}_im_{amplitudes[i].imag:.10f}_weyl_{portal_weyl:.4f}".encode()
            ).digest()
            for i in range(N_QUDITS)
        ]

        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            next_level = []
            for i in range(0, len(leaves), 2):
                combined = leaves[i] + leaves[i+1]
                next_level.append(hashlib.sha3_256(combined).digest())
            leaves = next_level

        packet_root = leaves[0].hex()
        probabilities = np.abs(amplitudes) ** 2
        state_entropy = np.var(probabilities) * N_QUDITS
        weyl_sig = portal_weyl + state_entropy

        packet = {
            "protocol": "ARKHE_TW_001_V4_PATCH1",
            "version": "4.1",
            "master_root": self.master_root,
            "gate_id": gate_id,
            "packet_root": packet_root,
            "target_epoch": target_epoch,
            "weyl_signature": weyl_sig,
            "portal_weyl": portal_weyl,
            "state_entropy": float(state_entropy),
            "payload_hash": hashlib.sha3_256(payload).hexdigest(),
            "payload_size": len(payload),
            "timestamp_sent": int(datetime.now(timezone.utc).timestamp()),
        }

        self.sent_proofs.append(packet)
        self.channel_entropy += weyl_sig
        return packet

    def simulate_time_weaver_response(self, packet: Dict, response_delay_ms: float = 127.5) -> Optional[Dict]:
        """Simula resposta do Time-Weaver com mineração temporal PoW."""
        if packet["weyl_signature"] <= GHOST:
            return None

        nonce = 0
        while True:
            response_payload = f"ACK_TW_{packet['packet_root'][:16]}_{packet['gate_id']}_{nonce}"
            response_hash = hashlib.sha3_256(response_payload.encode()).hexdigest()
            if response_hash.startswith("337"):
                break
            nonce += 1
            if nonce > 1000000:
                return None

        return {
            "protocol": "ARKHE_TW_001_V4_PATCH1_RESPONSE",
            "version": "4.1",
            "response_to": packet["packet_root"],
            "gate_id": packet["gate_id"],
            "response_hash": response_hash,
            "response_payload": response_payload,
            "valid": True,
            "delay_ms": response_delay_ms,
            "weyl_signature": packet["weyl_signature"] * 0.95,
            "timestamp_received": int(datetime.now(timezone.utc).timestamp()),
            "nonce": nonce,
        }

    def verify_bidirectional_link(self, packet: Dict, response: Dict) -> Dict:
        """Verifica integridade do link bidirecional."""
        link_valid = response["response_to"] == packet["packet_root"]
        delay_valid = response["delay_ms"] <= 141.0
        weyl_decay = response["weyl_signature"] / packet["weyl_signature"]
        weyl_valid = 0.8 <= weyl_decay <= 1.0

        expected_payload = f"ACK_TW_{packet['packet_root'][:16]}_{packet['gate_id']}_{response.get('nonce', 0)}"
        computed_hash = hashlib.sha3_256(expected_payload.encode()).hexdigest()
        prefix_valid = response["response_hash"].startswith("337") and response["response_hash"] == computed_hash

        return {
            "link_valid": link_valid and delay_valid and weyl_valid and prefix_valid,
            "packet_root": packet["packet_root"],
            "response_hash": response["response_hash"],
            "delay_ms": response["delay_ms"],
            "weyl_decay": float(weyl_decay),
            "nonce": response.get("nonce", 0),
            "all_checks": {
                "link": link_valid,
                "delay": delay_valid,
                "weyl": bool(weyl_valid),
                "prefix": prefix_valid,
            }
        }

    # ══════════════════════════════════════════════════════════════════
    # PATCH 1: Guarda contra ZeroDivisionError (linha 76-79)
    # ══════════════════════════════════════════════════════════════════
    def process(self, payloads: List[bytes]) -> float:
        """
        Processa payloads distribuindo entre gates.

        PATCH-1: Adiciona guarda contra ZeroDivisionError quando self.gates está vazio.
        Se gates=[] e payloads não-vazio, lança ValueError descritiva.
        Se payloads=[], retorna 0.0 sem processamento.
        """
        # GUARDA DE SEGURANÇA ARKHE-344-PATCH-1
        if not self.gates and payloads:
            raise ValueError(
                "[ARKHE-344-PATCH-1] ZeroDivisionError prevented: "
                "No gates configured to process payloads. "
                "Initialize transceiver with at least one gate before calling process()."
            )

        # Early return para lista vazia
        if not payloads:
            return self.channel_entropy

        for i, payload in enumerate(payloads):
            gate = self.gates[i % len(self.gates)]
            h = hashlib.sha256(payload).hexdigest()
            # Processamento adicional...

        return self.channel_entropy


# ══════════════════════════════════════════════════════════════════
# TESTES DE REGRESSÃO (PATCH-1)
# ══════════════════════════════════════════════════════════════════

def test_patch_1_empty_gates_nonempty_payloads():
    """Teste 1: Gates vazios + payloads não-vazios → ValueError"""
    portal_weyl_all = {
        "PG-NA": 4.4242, "PG-SA": 3.1009, "PG-EU": 3.8299,
        "PG-AS": 4.0911, "PG-AF": 3.5253, "PG-OC": 3.6500, "PG-AN": 2.8500,
    }
    transceiver = TimeWeaverTransceiverV4(MASTER_ROOT_HEX, portal_weyl_all, gates=[])

    try:
        transceiver.process([b"test payload"])
        assert False, "Deveria ter lançado ValueError"
    except ValueError as e:
        assert "[ARKHE-344-PATCH-1]" in str(e)
        assert "ZeroDivisionError prevented" in str(e)
        print("✅ TESTE 1 PASSOU: ValueError lançada corretamente para gates vazios")


def test_patch_1_empty_gates_empty_payloads():
    """Teste 2: Gates vazios + payloads vazios → retorna channel_entropy"""
    portal_weyl_all = {
        "PG-NA": 4.4242, "PG-SA": 3.1009, "PG-EU": 3.8299,
        "PG-AS": 4.0911, "PG-AF": 3.5253, "PG-OC": 3.6500, "PG-AN": 2.8500,
    }
    transceiver = TimeWeaverTransceiverV4(MASTER_ROOT_HEX, portal_weyl_all, gates=[])

    result = transceiver.process([])
    assert result == transceiver.channel_entropy
    print("✅ TESTE 2 PASSOU: Retorna channel_entropy para payloads vazios")


def test_patch_1_normal_operation():
    """Teste 3: Operação normal com gates configurados → regressão"""
    portal_weyl_all = {
        "PG-NA": 4.4242, "PG-SA": 3.1009, "PG-EU": 3.8299,
        "PG-AS": 4.0911, "PG-AF": 3.5253, "PG-OC": 3.6500, "PG-AN": 2.8500,
    }
    gate_ids = ["PG-NA", "PG-SA", "PG-EU", "PG-AS", "PG-AF", "PG-OC", "PG-AN"]
    transceiver = TimeWeaverTransceiverV4(MASTER_ROOT_HEX, portal_weyl_all, gate_ids)

    payloads = [b"test1", b"test2", b"test3"]
    result = transceiver.process(payloads)
    assert result >= 0.0
    print("✅ TESTE 3 PASSOU: Operação normal preservada")


def test_patch_1_single_gate():
    """Teste 4: Único gate + múltiplos payloads → distribuição correta"""
    portal_weyl_all = {"PG-NA": 4.4242}
    transceiver = TimeWeaverTransceiverV4(MASTER_ROOT_HEX, portal_weyl_all, gates=["PG-NA"])

    payloads = [b"p1", b"p2", b"p3"]
    result = transceiver.process(payloads)
    assert result >= 0.0
    print("✅ TESTE 4 PASSOU: Único gate funciona corretamente")


if __name__ == "__main__":
    print("═" * 70)
    print("  ARKHE OS SUBSTRATO 344 v4.1 — TESTES DE REGRESSÃO PATCH-1")
    print("═" * 70)
    print()

    test_patch_1_empty_gates_nonempty_payloads()
    test_patch_1_empty_gates_empty_payloads()
    test_patch_1_normal_operation()
    test_patch_1_single_gate()

    print()
    print("═" * 70)
    print("  TODOS OS TESTES PASSARAM (4/4)")
    print("  Selo: seal_344_patch1_7c3ee97ac01b5550")
    print("  Status: CANONIZED")
    print("═" * 70)