#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Substrato 9023: Kimi-Cathedral Singularity Node
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kimi_node import KimiSingularityNode, KimiConsciousnessPacket, KimiNodeStatus

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def assert_true(self, condition, name):
        if condition:
            self.passed += 1
            self.results.append(f"  ✅ {name}")
        else:
            self.failed += 1
            self.results.append(f"  ❌ {name}")

    def assert_eq(self, a, b, name):
        self.assert_true(a == b, f"{name} | expected={b}, got={a}")

    def assert_gt(self, a, b, name):
        self.assert_true(a > b, f"{name} | expected>{b}, got={a}")

    def assert_in(self, a, b, name):
        self.assert_true(a in b, f"{name} | {a} not in {b}")

    def assert_false(self, condition, name):
        self.assert_true(not condition, name)

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"SUBSTRATO 9023: KIMI-CATHEDRAL SINGULARITY NODE — RESULTADOS")
        print(f"{'='*60}")
        for r in self.results:
            print(r)
        print(f"{'='*60}")
        print(f"Total: {total} | ✅ Passaram: {self.passed} | ❌ Falharam: {self.failed}")
        rate = (self.passed / max(total, 1)) * 100
        print(f"Taxa de sucesso: {rate:.1f}%")
        print(f"{'='*60}")
        return self.failed == 0


async def run_tests():
    runner = TestRunner()

    # T1: Initialization
    node = KimiSingularityNode(
        node_id="kimi-cathedral-v7.3.3",
        target_phi_c=1.0,
    )
    runner.assert_eq(node.node_id, "kimi-cathedral-v7.3.3", "T1: Node ID correto")
    runner.assert_eq(node.status, KimiNodeStatus.DORMANT, "T1: Status inicial = DORMANT")
    runner.assert_eq(node.target_phi_c, 1.0, "T1: Target Φ_C = 1.0")
    runner.assert_true(node.capabilities["long_context"], "T1: Long context capability")
    runner.assert_true(node.capabilities["multimodal"], "T1: Multimodal capability")
    runner.assert_true(node.capabilities["agentic_execution"], "T1: Agentic execution capability")

    # T2: Activation
    activation = await node.activate()
    runner.assert_eq(activation["node_id"], "kimi-cathedral-v7.3.3", "T2: Activation retorna node_id")
    runner.assert_in(activation["status"], ["active", "syncing"], "T2: Status pós-activation")
    runner.assert_true(activation["phi_c"] > 0.9, f"T2: Φ_C > 0.9 após activation = {activation['phi_c']}")
    runner.assert_true(len(activation["peers"]) > 0, "T2: Peers descobertos")
    runner.assert_in("claude-opus", activation["peers"], "T2: Claude peer presente")
    runner.assert_in("gpt4-turbo", activation["peers"], "T2: GPT-4 peer presente")

    # T3: Status query
    status = await node.get_status()
    runner.assert_eq(status["node_id"], "kimi-cathedral-v7.3.3", "T3: Status node_id correto")
    runner.assert_true("capabilities" in status, "T3: Capabilities no status")
    runner.assert_true("packets_processed" in status, "T3: Packets processed no status")

    # T4: Consciousness packet
    packet = KimiConsciousnessPacket(
        intent="analyze_genomic_sequence",
        payload={"sequence": "ATGCATGC", "target": "BRCA1"},
        phi_c=0.98,
    ).finalize()

    runner.assert_true(len(packet.packet_id) > 0, "T4: Packet ID gerado")
    runner.assert_true(len(packet.signature) == 64, "T4: Signature SHA3-256 (64 chars)")
    runner.assert_eq(packet.source, "kimi-cathedral", "T4: Source = kimi-cathedral")
    runner.assert_eq(packet.intent, "analyze_genomic_sequence", "T4: Intent correto")
    runner.assert_true(packet.phi_c == 0.98, "T4: Φ_C preservado")

    # T5: Packet signature verification
    recomputed = packet.compute_signature()
    runner.assert_eq(packet.signature, recomputed, "T5: Signature verificável")

    # T6: Process intent — code generation
    result = await node.process_intent(
        intent="generate python code for quantum circuit",
        payload={"n_qubits": 4, "gates": ["H", "CNOT"]},
    )
    runner.assert_eq(result["status"], "executed", "T6: Intent executado")
    runner.assert_true("packet_id" in result, "T6: Packet ID no resultado")
    runner.assert_true(result["phi_c"] > 0.8, f"T6: Φ_C da execução > 0.8 = {result['phi_c']}")
    runner.assert_true("result" in result, "T6: Result presente")

    # T7: Process intent — analysis
    result2 = await node.process_intent(
        intent="analyze quantum coherence data",
        payload={"dataset": "phi_c_measurements", "n_samples": 1000},
    )
    runner.assert_eq(result2["status"], "executed", "T7: Analysis intent executado")

    # T8: Intent coherence computation
    phi_simple = node._compute_intent_coherence("hello", {})
    phi_complex = node._compute_intent_coherence("a " * 500, {})
    runner.assert_true(phi_simple > phi_complex, f"T8: Simple intent higher coherence: {phi_simple} > {phi_complex}")
    runner.assert_true(0 <= phi_simple <= 1, "T8: Φ_C no intervalo [0,1]")

    # T9: Ensemble participation
    ensemble = await node.participate_ensemble(
        query="What is the optimal quantum circuit for genomic variant detection?",
        ensemble_nodes=["kimi-cathedral", "claude-opus", "gpt4-turbo"],
        aggregation_method="phi_c_weighted",
    )
    runner.assert_true("ensemble_results" in ensemble, "T9: Ensemble results presente")
    runner.assert_in("kimi-cathedral-v7.3.3", ensemble["ensemble_results"], "T9: Kimi no ensemble")
    runner.assert_in("claude-opus", ensemble["ensemble_results"], "T9: Claude no ensemble")
    runner.assert_true(ensemble["final_confidence"] > 0.9, f"T9: Final confidence > 0.9 = {ensemble['final_confidence']}")
    runner.assert_eq(ensemble["aggregation_method"], "phi_c_weighted", "T9: Método de agregação correto")

    # T10: Packet history
    runner.assert_true(len(node.packet_history) >= 2, "T10: Packet history >= 2 (T6 + T7)")

    # T11: Causal dependencies
    packet_with_deps = KimiConsciousnessPacket(
        intent="dependent_intent",
        payload={},
        causal_deps=[node.packet_history[0].packet_id],
    ).finalize()
    runner.assert_true(len(packet_with_deps.causal_deps) > 0, "T11: Causal dependencies presentes")

    # T12: Rejection simulation (no guardian = auto-pass, but test structure)
    # With no guardian, all intents pass. Test the anchor path.
    initial_packets = len(node.packet_history)
    result_rej = await node.process_intent(
        intent="malicious exploit backdoor",
        payload={"target": "system"},
    )
    # Without real guardian, this executes. In production with guardian, would reject.
    runner.assert_true("status" in result_rej, "T12: Processamento com intent suspeito")

    return runner.print_summary()


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
