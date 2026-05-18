#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from substrate_240_vitalik.lean_bridge.lean_to_beaver import LeanToBeaver
from substrate_240_vitalik.assembly_verifier.smt_verifier import SMTAssemblyVerifier
import logging

logging.basicConfig(level=logging.INFO)

def verify_equiv(assembly_code, lang, spec_code, spec_lang):
    verifier = SMTAssemblyVerifier()
    return verifier.verify_equivalence(assembly_code, lang, spec_code, spec_lang)


def seal(intent, assembly_code, proof):
    class DummyToken:
        def __init__(self):
            self.header = "arkhe:token:vitalik_240_mock"
            self.seal = "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    return DummyToken()

intent = "transferir 100 USDC de A para B"

lean_spec = """
theorem transfer_preserves_total_supply (before after : ledger) :
    total_supply before = total_supply after := by
  simp
"""

assembly_code = """
    PUSH1 0x64
    PUSH1 0x00
    MSTORE
"""

converter = LeanToBeaver()
proof = converter.convert(lean_spec)

if proof:
    wasm_code = 'i32.const 100\ni32.const 0\ni32.add'
    is_valid = verify_equiv(assembly_code, 'EVM', wasm_code, 'WASM')
    if is_valid:
        token = seal(intent, assembly_code, proof)
        print(f'Token Arkhe: {token.header}')
        print(f'Selo de Verificação: {token.seal}')
