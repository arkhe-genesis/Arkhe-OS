# arkhe_os/release/ocaml_bindings.py
"""Bindings Python para funções OCaml de verificação Octra via js_of_ocaml ou ctypes."""

import ctypes
import json
import os
from pathlib import Path

# Tentar carregar biblioteca OCaml compilada
try:
    # Compilar OCaml para shared library
    # ocamlopt -shared -o liboctra_verifier.so octra_verifier_zarith.ml -cclib -lzarith
    lib_path = Path(__file__).parent / "liboctra_verifier.so"
    if lib_path.exists():
        lib = ctypes.CDLL(str(lib_path))

        # Definir signatures das funções
        lib.verify_release_integrity.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        lib.verify_release_integrity.restype = ctypes.c_bool

        lib.compute_canonical_seal.argtypes = [ctypes.c_char_p]
        lib.compute_canonical_seal.restype = ctypes.c_char_p

        def verify_release_integrity(components_json: str, expected_seal: str) -> bool:
            return lib.verify_release_integrity(
                components_json.encode(),
                expected_seal.encode()
            )

        def compute_canonical_seal(components_json: str) -> str:
            result = lib.compute_canonical_seal(components_json.encode())
            return result.decode()

    else:
        raise ImportError("liboctra_verifier.so not found")

except (ImportError, OSError):
    # Fallback: compilar via js_of_ocaml para Wasm e usar Pyodide
    # Ou usar implementação Python pura de Zarith (mais lenta)
    # Mocking Zarith since zarith_python does not exist natively in pip usually
    class Z:
        def __init__(self, val):
            if isinstance(val, str):
                if val.startswith("0x"):
                    self.val = int(val, 16)
                else:
                    self.val = int(val)
            else:
                self.val = val
        def __add__(self, other):
            return Z(self.val + other.val)
        def __mul__(self, other):
            return Z(self.val * other.val)
        def __mod__(self, other):
            return Z(self.val % other.val)
        def __int__(self):
            return self.val

    VERIFICATION_PRIME = Z(
        "115792089237316195423570985008687907853269984665640564039457584007913129639937"
    )

    def hex_to_z(hex_str: str) -> Z:
        return Z(int(hex_str, 16))

    def z_to_hex(z: Z) -> str:
        return hex(int(z))[2:]

    def compute_canonical_seal(components_json: str) -> str:
        components = json.loads(components_json)
        weighted_sum = Z(0)
        for comp in components:
            hash_z = hex_to_z(comp["hash"])
            weight_z = Z(comp["weight"])
            weighted_sum = weighted_sum + (hash_z * weight_z)
        seal = weighted_sum % VERIFICATION_PRIME
        return z_to_hex(seal)

    def verify_release_integrity(components_json: str, expected_seal: str) -> bool:
        computed = compute_canonical_seal(components_json)
        return computed == expected_seal
