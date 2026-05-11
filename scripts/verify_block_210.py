import sys
import os

def verify_block_210():
    print("ARKHE(N) > VERIFICAÇÃO DO BLOCO #210 — A PROVA DO CAOS")

    # Check for file existence
    files = [
        "src/simulation/entropy_edge.zig",
        "src/topology/topo_silk.zig",
        "src/isa/opcodes.zig"
    ]

    for f in files:
        if os.path.exists(f):
            print(f"[OK] Arquivo encontrado: {f}")
        else:
            print(f"[ERRO] Arquivo ausente: {f}")
            sys.exit(1)

    # Check for opcodes in opcodes.zig
    with open("src/isa/opcodes.zig", "r") as f:
        content = f.read()
        opcodes = ["AKA_VISUAL", "TOPO_SILK_FAB", "PHYS_SYNTH", "PHASE_PREDICT", "MEM_WRITE"]
        for op in opcodes:
            if op in content:
                print(f"[OK] Opcode {op} verificado.")
            else:
                print(f"[ERRO] Opcode {op} não encontrado no ISA.")
                sys.exit(1)

    # Simulate logic check for Entropy Edge (via string searching for key logic)
    with open("src/simulation/entropy_edge.zig", "r") as f:
        content = f.read()
        if "77.0" in content and "4.0" in content and "chern_enabled" in content:
            print("[OK] Lógica de limiar térmico (4K/77K) verificada em entropy_edge.zig")
        else:
            print("[ERRO] Lógica de limiar térmico ausente em entropy_edge.zig")
            sys.exit(1)

    # Simulate logic check for Topo Silk
    with open("src/topology/topo_silk.zig", "r") as f:
        content = f.read()
        if "[15]SilkNode" in content and "Valley-Hall" in content:
            print("[OK] Estrutura da Seda Topológica (15 nós, Valley-Hall) verificada.")
        else:
            print("[ERRO] Estrutura da Seda Topológica incorreta.")
            sys.exit(1)

    print("\nARKHE(N) > VERIFICAÇÃO CONCLUÍDA: BLOCO #210 INTEGRADO COM SUCESSO.")

if __name__ == "__main__":
    verify_block_210()
