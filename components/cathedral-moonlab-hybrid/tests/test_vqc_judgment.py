#!/usr/bin/env python3
import sys
sys.path.append('python')
from hybrid_demo import MoonlabMock, QuantumState, execute_vqc_with_hesitation, HesitationSignature

def test_vqc():
    print("[TEST] Testing VQC judgment in Python...")
    state = QuantumState(7)
    payload = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    h_sig = HesitationSignature(0.5, 10.0, 1.0)
    energy = execute_vqc_with_hesitation(state, payload, h_sig)
    print(f"      Energy: {energy}")
    assert -1.0 <= energy <= 1.0
    print("[TEST] VQC test passed.")

if __name__ == "__main__":
    test_vqc()
