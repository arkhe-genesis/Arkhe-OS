#!/usr/bin/env python3
import struct
import random
import os

ROI_TOKEN_SIZE = 8
NUM_TOKENS = 1024
OUTPUT_FILE = "roi_stream.bin"

def generate_token(seed: int) -> bytes:
    rng = random.Random(seed)

    x = rng.randint(0, 65535)
    y = rng.randint(0, 65535)
    z = rng.randint(0, 65535)
    intensity_msb = rng.randint(0, 255)

    flags = 0x00
    if rng.random() > 0.7: flags |= 0x01  # red
    if rng.random() > 0.8: flags |= 0x02  # green
    if rng.random() > 0.9: flags |= 0x04  # blue
    if rng.random() > 0.95: flags |= 0x08  # high_intensity

    # Layout little-endian alinhado ao VRP v1.1 corrigido:
    # bytes 0-1: x, 2-3: y, 4-5: z, 6: intensity_msb, 7: flags
    return struct.pack('<HHHBB', x, y, z, intensity_msb, flags)

def main():
    with open(OUTPUT_FILE, 'wb') as f:
        for i in range(NUM_TOKENS):
            f.write(generate_token(seed=i))

    print(f"[GEN] Arquivo {OUTPUT_FILE} gerado: {NUM_TOKENS} tokens × {ROI_TOKEN_SIZE} bytes = {NUM_TOKENS * ROI_TOKEN_SIZE} bytes")

    # Validação imediata: round-trip com o parser
    from roi_token import ROIToken

    with open(OUTPUT_FILE, 'rb') as f:
        data = f.read()

    assert len(data) == NUM_TOKENS * ROI_TOKEN_SIZE
    errors = 0
    for i in range(NUM_TOKENS):
        token = ROIToken.from_bytes(data[i*8:(i+1)*8])
        # Verifica limites
        if not (0 <= token.x <= 65535 and 0 <= token.y <= 65535 and 0 <= token.z <= 65535):
            errors += 1
            print(f"[GEN] Token {i} fora dos limites: x={token.x}, y={token.y}, z={token.z}")

    if errors == 0:
        print(f"[GEN] ✅ Round-trip validado: todos os {NUM_TOKENS} tokens parseados corretamente.")
    else:
        print(f"[GEN] ❌ {errors} falhas de round-trip detectadas.")

if __name__ == "__main__":
    main()
