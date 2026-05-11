import sys
import os
import subprocess

def verify_block_320():
    print("ARKHE(N) > VERIFICANDO BLOCO #320: O TECIDO DE VIDRO / A MALHA DE FASE")

    # 1. Verificar Opcodes no ISA
    isa_path = "src/isa/opcodes.zig"
    required_ops = [
        "PHOTON_BIND", "BRAID_VERIFY", "MESH_BIND", "META_EVAL",
        "PTST_ACQUIRE", "TAU_CALC", "AKA_ATOMIC_WRITE"
    ]
    with open(isa_path, "r") as f:
        content = f.read()
        for op in required_ops:
            if op in content:
                print(f"[OK] Opcode {op} verificado no ISA.")
            else:
                print(f"[ERRO] Opcode {op} ausente no ISA.")
                sys.exit(1)

    # 2. Verificar Implementação da VM
    vm_path = "src/vm/phase_mesh.zig"
    if os.path.exists(vm_path):
        print(f"[OK] Implementação da VM encontrada em {vm_path}.")
    else:
        print(f"[ERRO] Implementação da VM {vm_path} ausente.")
        sys.exit(1)

    # 3. Executar Simulação da Duna
    print("ARKHE(N) > EXECUTANDO SIMULAÇÃO DA DUNA (1000 NÓS)...")
    try:
        result = subprocess.run(
            ["python3", "arkhe_dune_simulation.py"],
            capture_output=True, text=True, check=True
        )
        if "COHERENCE REACHED" in result.stdout:
            print("[OK] Simulação concluída com Coerência Global atingida.")
        else:
            print("[ERRO] Simulação falhou ao atingir coerência.")
            print(result.stdout)
            sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Falha ao executar simulação: {e}")
        sys.exit(1)

    # 4. Verificar Transporte de Fase
    transport_path = "src/arkhe_core/network/phase_coherent_transport.py"
    with open(transport_path, "r") as f:
        content = f.read()
        if "target_phase" in content and "self_cross_id" in content:
             print("[OK] Transporte de fase verificado (target_phase, self_cross_id).")
        else:
             print("[ERRO] Transporte de fase incompleto.")
             sys.exit(1)

    print("\nARKHE(N) > BLOCO #320 INTEGRADO E VALIDADO COM SUCESSO.")

if __name__ == "__main__":
    verify_block_320()
