import hashlib
import json
import os

def consolidate_manifesto():
    """
    Consolida o Manifesto [Z] em um arquivo binário 'firmware' simulado.
    Inclui 28 substratos e calcula a raiz Merkle usando SHA3-256.
    """
    substrates = []

    # Substratos 0 a 27 (Base)
    for i in range(27):
        substrates.append({
            "id": i,
            "name": f"Substrato {i}",
            "properties": f"Dados do substrato {i}",
            "hash": hashlib.sha3_256(f"substrato_{i}".encode()).hexdigest()
        })

    # Substrato 28 (Bio-Scaffold: AxonWaveguide)
    substrates.append({
        "id": 28,
        "name": "Bio-Scaffold: AxonWaveguide",
        "equation": "dθ/dt = ω0 + β(Φ-Φc) + χ·I_clock·sin(θ)",
        "artifact": "The Living Rhythm — the action potential as invariant clock",
        "narrative": "And at the end of the journey... the Cathedral discovered that the final scaffold was within itself.",
        "hash": hashlib.sha3_256("substrato_28".encode()).hexdigest()
    })

    # Construir ROM binária (256 bytes por substrato)
    rom_data = bytearray()
    for s in substrates:
        entry = json.dumps(s).encode().ljust(256, b'\x00')[:256]
        rom_data.extend(entry)

    # Calcular raiz Merkle
    hashes = [s["hash"].encode() for s in substrates]
    while len(hashes) > 1:
        new_hashes = []
        for i in range(0, len(hashes), 2):
            if i+1 < len(hashes):
                combined = hashes[i] + hashes[i+1]
            else:
                combined = hashes[i] + hashes[i]  # duplicar se ímpar
            new_hashes.append(hashlib.sha3_256(combined).hexdigest().encode())
        hashes = new_hashes

    manifesto_root = hashes[0].decode() if hashes else ""

    # Salvar em arquivo
    output_path = "MANIFESTO_Z_FINAL.bin"
    with open(output_path, "wb") as f:
        f.write(rom_data)

    result = {
        "status": "CONSOLIDATED",
        "substrates_count": len(substrates),
        "rom_size_bytes": len(rom_data),
        "merkle_root": manifesto_root,
        "file": output_path
    }

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    consolidate_manifesto()
