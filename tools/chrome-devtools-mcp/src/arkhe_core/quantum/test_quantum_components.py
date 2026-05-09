"""
Integration Test for ARKHE-Q Components
Verifies Syndrome Registry and VQC Inquisitor interaction.
"""

import sys
import os
import logging
import json

# Adiciona o diretório src ao path para importação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))

from arkhe_core.quantum.syndrome_registry import QuantumSyndromeRegistry
from arkhe_core.quantum.vqc_inquisitor import VQCInquisitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ARKHE-Q-TEST")

def test_arkhe_q_integration():
    logger.info("Starting ARKHE-Q Integration Test...")

    # 1. Initialize Components
    quartz_seal = "CRYO-FINAL-001-B8E4D3"
    registry = QuantumSyndromeRegistry("ROOT_ALPHA", quartz_seal)
    inquisitor = VQCInquisitor(num_qubits=4, num_layers=2)

    # 2. Simulate Payload Processing
    payloads = [
        ("GET /api/v1/status", "ALLOW"),
        ("DROP TABLE users; --", "DENY"),
        ("\x00Sussurro\xff", "HESITATE")
    ]

    for payload, expected_min_verdict in payloads:
        logger.info(f"Processing Payload: {payload}")

        # Inquisitor Judge
        verdict, score = inquisitor.judge(payload)
        logger.info(f"VQC Verdict: {verdict} (Score: {score:.4f})")

        # If any anomaly detected or suspicious score, register syndrome
        # (In our case, we register every attempt as a 'testimony')
        syndrome = (1 if score > 0.5 else 0, 1 if score > 0.7 else 0)
        intensity = int(score * 65535)

        entry = registry.register_event(
            syndrome=syndrome,
            intensity=intensity,
            t2_star=142.0,
            witnesses=["ROOT_BETA"]
        )

        registry.validate_mesh_event(entry)

    # 3. Final Verification
    ledger_data = json.loads(registry.get_ledger_json())
    assert len(ledger_data) == len(payloads)
    assert registry.current_coherence < 1.0

    logger.info("ARKHE-Q Integration Test: SUCCESS")
    print("\n--- Final Syndrome Ledger ---")
    print(registry.get_ledger_json())

if __name__ == "__main__":
    try:
        test_arkhe_q_integration()
    except Exception as e:
        logger.error(f"Test Failed: {e}")
        sys.exit(1)
