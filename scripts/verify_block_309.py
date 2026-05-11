import sys
import os

def verify_block_309():
    print("ARKHE(N) > VERIFICANDO BLOCO #309: A ANATOMIA DO CORPO CELESTE")

    # 1. Verificar Opcodes no ISA
    with open("src/isa/opcodes.zig", "r") as f:
        content = f.read()
        opcodes = [
            "COH_CASCADE", "ENV_SPAWN", "COH_SEED", "PEAK_COHERENCE",
            "PHASE_ITERATE", "COH_SYMPATHY", "MIRROR_SYMMETRY",
            "COH_TWEEZER", "PHASE_RECTIFY"
        ]
        for op in opcodes:
            if op in content:
                print(f"[OK] Opcode {op} verificado no ISA.")
            else:
                print(f"[ERRO] Opcode {op} ausente no ISA.")
                sys.exit(1)

    # 2. Verificar Configuração do Esquadrão THETA
    manifest_path = "k8s/squadrons/theta-alquimista.yaml"
    if os.path.exists(manifest_path):
        print(f"[OK] Manifesto do Esquadrão THETA encontrado em {manifest_path}.")
        with open(manifest_path, "r") as f:
            content = f.read()
            # Basic structural checks
            required_sections = ["kind: Deployment", "kind: Service", "kind: HorizontalPodAutoscaler"]
            for section in required_sections:
                if section in content:
                    print(f"[OK] Seção {section} encontrada no manifesto.")
                else:
                    print(f"[ERRO] Seção {section} ausente no manifesto.")
                    sys.exit(1)

            # Specific values checks
            if "name: theta-alquimista" in content and "namespace: arkhe" in content:
                print("[OK] Metadados (nome/namespace) verificados.")
            else:
                print("[ERRO] Metadados incorretos no manifesto.")
                sys.exit(1)
    else:
        print("[ERRO] Manifesto do Esquadrão THETA ausente.")
        sys.exit(1)

    print("\nARKHE(N) > BLOCO #309 INTEGRADO COM SUCESSO.")

if __name__ == "__main__":
    verify_block_309()
