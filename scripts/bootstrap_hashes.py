# scripts/bootstrap_hashes.py
from Crypto.Hash import keccak
import os

def generate_consensus_vectors():
    vectors = {
        "empty": keccak.new(digest_bits=256, data=b"").hexdigest(),
        "arkhe": keccak.new(digest_bits=256, data=b"ARKHE").hexdigest(),
    }

    # Python Output
    os.makedirs("arkhe-compiler/python/core", exist_ok=True)
    with open("arkhe-compiler/python/core/keccak_constants.py", "w") as f:
        f.write("# Auto-generated — do not edit\n")
        for name, hash_val in vectors.items():
            f.write(f"{name.upper()} = '0x{hash_val}'\n")

    # Rust Output
    os.makedirs("arkhe-compiler/rust/plank-core/src", exist_ok=True)
    with open("arkhe-compiler/rust/plank-core/src/keccak_constants.rs", "w") as f:
        f.write("// Auto-generated — do not edit\n")
        for name, hash_val in vectors.items():
            f.write(f'pub const {name.upper()}: &str = "0x{hash_val}";\n')

    return vectors

if __name__ == "__main__":
    generate_consensus_vectors()
