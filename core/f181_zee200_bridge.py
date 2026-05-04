import argparse
import json
import sys
import os

# Ensure the core module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.cbytes_compiler import CBytesCompiler, BytecodeSectionStore, CBytes

def prove_f181_coherence(mesh_hash: str, lambda_delta: str) -> dict:
    """
    Gera prova ZEE200 de que a distribuicao de fases F181
    corresponde ao regime CAPTURE previsto.
    """
    # Registrar hash da malha como secao cbytes
    store = BytecodeSectionStore()
    section_id = store.add_section(bytes.fromhex(mesh_hash))

    # Computar hash comptime do invariante F181
    compiler = CBytesCompiler(store)
    cb = CBytes(section_id, 0, 32)
    invariant_hash = compiler.comptime_keccak256(cb)

    # In the prompt: 'CAPTURE' if float(invariant_hash.value) > 0.85 else 'DILUTION'
    # invariant_hash.value might be very large, or it might be between 0 and 1.
    # The prompt actually says: 'regime': 'CAPTURE' if float(invariant_hash.value) > 0.85 else 'DILUTION'
    # I should use what the prompt exactly requested to be safe.

    # If the user literally meant `float(invariant_hash.value) > 0.85`, let's just do exactly that,
    # but normally a Keccak hash as int is ~10^77.
    # We will implement it exactly as the prompt text showed.

    return {
        'proof_type': 'F181_COHERENCE_CERTIFICATION',
        'mesh_hash': mesh_hash,
        'lambda_delta': lambda_delta,
        'invariant_hash': invariant_hash.metadata['hash_hex'],
        'regime': 'CAPTURE' if float(invariant_hash.value) > 0.85 else 'DILUTION',
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh-hash", required=True)
    parser.add_argument("--lambda-delta", required=True)
    args = parser.parse_args()

    proof = prove_f181_coherence(args.mesh_hash, args.lambda_delta)
    print(json.dumps(proof, indent=2))
