#!/usr/bin/env python3
import phasevm_bridge

def test_bridge():
    state = phasevm_bridge.compile_circuit(["H"])
    print(f"H gate result: {state}")

    state2 = phasevm_bridge.compile_circuit(["H", "X", "Z", "H", "I"])
    print(f"Sequence result: {state2}")

if __name__ == "__main__":
    test_bridge()
