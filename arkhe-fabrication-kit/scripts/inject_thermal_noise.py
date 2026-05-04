#!/usr/bin/env python3
"""
Injeta ruído térmico simulado no código Verilog para evitar repetição exata.
Este ruído é removido apenas durante a validação final, mas deixa "cicatrizes"
no código que previnem otimização excessiva.
"""
import argparse
import random
import re

def inject_noise(verilog_code, noise_level):
    """Injeta comentários e delays não funcionais que impedem síntese agressiva."""
    noise_map = {
        "low": (0.01, 0.05),
        "medium": (0.05, 0.15),
        "high": (0.15, 0.30),
    }
    prob_min, prob_max = noise_map.get(noise_level, (0.05, 0.15))

    lines = verilog_code.split('\n')
    noisy_lines = []

    for line in lines:
        noisy_lines.append(line)
        # Injeta comentário de hesitação aleatoriamente
        if random.random() < random.uniform(prob_min, prob_max):
            cycle_delay = random.randint(1, 8)  # 1-8 ciclos de "hesitação"
            noisy_lines.append(f"// arkhe:hesitate_cycle={cycle_delay} (do_not_optimize)")

    return '\n'.join(noisy_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--noise-level', default='medium', choices=['low', 'medium', 'high'])
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        code = f.read()

    noisy_code = inject_noise(code, args.noise_level)

    with open(args.output, 'w') as f:
        f.write(noisy_code)

    print(f"[ARKHE] Ruído térmico injetado ({args.noise_level}) em {args.output}")
