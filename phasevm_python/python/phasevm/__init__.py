# phasevm_python/python/phasevm/__init__.py
from .phasevm_rs import PyPhaseVM as _PhaseVM

class PhaseVM:
    """Pythonic wrapper for Rust PhaseVM JIT compiler."""

    def __init__(self):
        self._vm = _PhaseVM()

    def compile_circuit(self, gates: list[str]) -> complex:
        """Compile topological bytecode to native code and return Jones invariant."""
        re, im = self._vm.compile_circuit(gates)
        return complex(re, im)

    def clear_cache(self):
        """Clear JIT compilation cache."""
        self._vm.clear_cache()

    @property
    def cache_size(self) -> tuple[int, int]:
        """Return (circuit_cache_size, gate_cache_size)."""
        return self._vm.cache_stats()
