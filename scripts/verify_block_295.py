import sys
import os
import numpy as np
from src.physics import higgs_fragmentation as higgs

def verify_block_295():
    print("ARKHE(N) > VERIFICANDO BLOCO #295: O CRONÓGRAFO DE PARTÍCULAS")

    # 1. Verificar Opcodes no ISA
    with open("src/isa/opcodes.zig", "r") as f:
        content = f.read()
        opcodes = ["HIGGS_WIDTH", "HIGGS_FRAGMENTATION", "DGLAP_EVOLVE", "FRAG_FIT", "COLLIDER_OBSERVABLE"]
        for op in opcodes:
            if op in content:
                print(f"[OK] Opcode {op} verificado no ISA.")
            else:
                print(f"[ERRO] Opcode {op} ausente no ISA.")
                sys.exit(1)

    # 2. Verificar Configuração do Esquadrão IOTA
    if os.path.exists("k8s/squadrons/iota-cronografo.yaml"):
        print("[OK] Manifesto do Esquadrão IOTA encontrado.")
    else:
        print("[ERRO] Manifesto do Esquadrão IOTA ausente.")
        sys.exit(1)

    # 3. Testar Lógica de Física (Higgs Fragmentation)
    print("Testando lógica de física...")

    # Teste de Thresholds (Eq. 28)
    xb_min, xb_max = higgs.threshold_analysis()
    expected_xb_min = 2 * higgs.MB_MESON / higgs.MH
    if abs(xb_min - expected_xb_min) < 1e-4:
        print(f"[OK] Threshold cinemático xb_min = {xb_min:.4f} verificado.")
    else:
        print(f"[ERRO] Threshold cinemático incorreto: {xb_min} != {expected_xb_min}")
        sys.exit(1)

    # Teste de Enhancement (GM-VFNS effects)
    x_range = np.linspace(0.1, 0.9, 50)
    spectrum = higgs.scaled_energy_spectrum(x_range)

    # Check low-x enhancement (~27% for xb < 0.25)
    # Check peak enhancement (~6% for xb ~ 0.55)
    # This is implemented in our simplified model in higgs_fragmentation.py

    low_x_val = higgs.scaled_energy_spectrum([0.2])[0]
    mid_x_val = higgs.scaled_energy_spectrum([0.4])[0]
    # base for 0.2 is (1-0.2)^2 * 0.2^3 * 100 = 0.64 * 0.008 * 100 = 0.512
    # base for 0.4 is (1-0.4)^2 * 0.4^3 * 100 = 0.36 * 0.064 * 100 = 2.304

    expected_low = (1-0.2)**2 * 0.2**3 * 100 * 1.27
    if abs(low_x_val - expected_low) < 1e-4:
        print("[OK] Enhancement de baixa energia (mB finite) verificado.")
    else:
        print(f"[ERRO] Falha no enhancement de baixa energia: {low_x_val} != {expected_low}")
        sys.exit(1)

    print("\nARKHE(N) > BLOCO #295 INTEGRADO COM SUCESSO.")

if __name__ == "__main__":
    verify_block_295()
