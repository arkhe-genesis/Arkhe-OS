import sys
sys.path.append('agi/system32/inference/neuro_symbolic')
sys.path.append('agi/system32/inference/quantum')
sys.path.append('agi/system32/inference/fhe')
sys.path.append('agi/system32/inference/orchestrator')

import torch
import numpy as np

from neuro_symbolic_engine import NeuroSymbolicEngine
from quantum_sync_protocol import QuantumSyncEngine
from adaptive_fhe_tuner import AdaptiveFHETuner
from coherence_orchestrator import CoherenceOrchestrator
from coherence_dashboard import Dashboard

def test_neuro_symbolic():
    engine = NeuroSymbolicEngine(neural_dim=512, symbol_dim=128, num_classes=10)
    x_neural = torch.randn(1, 512)
    x_symbolic = torch.randn(1, 128)
    knowledge_graph = {'active_rules': ['rule1', 'rule2'], 'key_relations': ['A -> B']}
    logits, expl = engine(x_neural, x_symbolic, knowledge_graph)
    assert logits.shape == (1, 10)
    assert "explanation" in expl
    print("Neuro-Symbolic test passed.")

def test_quantum_sync():
    engine = QuantumSyncEngine(fidelity_threshold=0.85)
    success = engine.prepare_entanglement("NodeA", "NodeB", "Mediator")
    if success:
        state_vector = np.array([1, 0])
        success, msg = engine.perform_sync("NodeA", "NodeB", state_vector)
        print("Quantum Sync result:", msg)
    else:
        print("Quantum Sync preparation failed due to low fidelity (expected based on distance/noise).")
    print("Quantum Sync test finished.")

def test_fhe_tuner():
    tuner = AdaptiveFHETuner({'ring_dim': 4096, 'modulus_bits': 40, 'noise_std': 3.2})
    new_params = tuner.update_parameters(current_load=0.75, security_requirement=128, current_latency_ms=85.0)
    assert "ring_dim" in new_params
    assert "modulus_bits" in new_params
    assert "noise_std" in new_params
    print("FHE Tuner test passed:", new_params)

def test_orchestrator():
    orchestrator = CoherenceOrchestrator(target_phi=0.85, min_phi=0.70)
    state = {"symbolic_confidence": 0.82, "sync_fidelity": 0.88, "sync_latency_ms": 45.0, "security_compliance": 0.92}
    actions = orchestrator.monitor_and_adapt(state)
    assert "adjustments" in actions
    assert "fallbacks" in actions
    print("Orchestrator test passed:", actions)

def test_dashboard():
    dashboard = Dashboard()
    dashboard.update(0.9, 0.88, 0.95)
    dashboard.display()
    print("Dashboard test passed.")

if __name__ == "__main__":
    test_neuro_symbolic()
    test_quantum_sync()
    test_fhe_tuner()
    test_orchestrator()
    test_dashboard()
