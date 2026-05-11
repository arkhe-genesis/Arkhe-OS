#!/usr/bin/env python3
"""
Python Bridge to PhaseVM Rust JIT Compiler.
Provides a mock implementation for testing if the rust library isn't available.
"""
import ctypes
import os
import sys

# Attempt to load the Rust library via ctypes (or a mock if it fails)
class PhaseVMMock:
    def __init__(self):
        self.cache = {}
        self.gates = {
            "I": complex(1.0, 0.0),
            "H": complex(0.70710678, 0.0),
            "X": complex(0.0, 1.0), # Simplified for mock
            "Z": complex(1.0, 0.0)  # Simplified for mock
        }
        print("Initialized PhaseVM Mock")

    def compile_circuit(self, gates):
        key = "|".join(gates)
        if key in self.cache:
            return self.cache[key]

        # Simple evaluation mock
        state = complex(1.0, 0.0)
        for g in gates:
            if g == "H":
                state *= complex(0.70710678, 0.0)
            elif g == "X":
                # Mock effect of X gate
                state = complex(state.imag, state.real)
            elif g == "Z":
                state = complex(state.real, -state.imag)

        self.cache[key] = state
        return state

    def clear_cache(self):
        self.cache.clear()

class PyAsyncPhaseVMMock:
    def __init__(self, num_workers=2):
        self.mock = PhaseVMMock()
        self.stats = {"circuit_cache_size": 0, "gate_cache_size": 4}

    async def compile_circuit_async(self, gates, timeout_ms=50.0):
        res = self.mock.compile_circuit(gates)
        # Mock cache hit behavior
        cache_hit = "|".join(gates) in self.mock.cache
        return (res.real, res.imag, cache_hit)

    def get_cache_stats(self):
        return (len(self.mock.cache), self.stats["gate_cache_size"])

    def clear_cache(self):
        self.mock.clear_cache()

    def warmup_cache(self, circuits):
        for circuit in circuits:
            self.mock.compile_circuit(circuit)

# Try to load actual compiled rust extension, fallback to mock
try:
    import phasevm_rs
    PhaseVM = phasevm_rs.PyPhaseVM
    PyAsyncPhaseVM = phasevm_rs.PyAsyncPhaseVM
except ImportError:
    PhaseVM = PhaseVMMock
    PyAsyncPhaseVM = PyAsyncPhaseVMMock

phasevm = PhaseVM()

def compile_circuit(gates):
    """Compile topological bytecode to native code and execute."""
    return phasevm.compile_circuit(gates)

def clear_cache():
    """Clear JIT compilation cache."""
    phasevm.clear_cache()
