import os
import sys

def verify_opcode():
    print("ARKHE(N) > VERIFICANDO BLOCO #393: ARKHE-GNU")
    with open("src/isa/opcodes.zig", "r") as f:
        content = f.read()
        if "GNU_COMPAT" in content:
            print("[OK] Opcode GNU_COMPAT verificado no ISA.")
        else:
            print("[ERRO] Opcode GNU_COMPAT ausente no ISA.")
            return False
    return True

def verify_tools():
    tools_file = "src/tools/arkhe_gnu.ts"
    if not os.path.exists(tools_file):
        print(f"[ERRO] Arquivo {tools_file} não encontrado.")
        return False

    with open(tools_file, "r") as f:
        content = f.read()
        required = ["arkheGnu", "als", "acp", "amv", "agrep", "amake"]
        for tool in required:
            if tool in content:
                print(f"[OK] Ferramenta {tool} verificada.")
            else:
                print(f"[ERRO] Ferramenta {tool} ausente.")
                return False
    return True

if __name__ == "__main__":
    if verify_opcode() and verify_tools():
        print("\nARKHE(N) > BLOCO #393 INTEGRADO COM SUCESSO.")
        sys.exit(0)
    else:
        print("\nARKHE(N) > FALHA NA VERIFICAÇÃO DO BLOCO #393.")
        sys.exit(1)
